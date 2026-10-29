#include "logger_power.h"
#include <Arduino.h>
#include <lwIP_CYW43.h>
#include <pico/cyw43_arch.h>
#include <pico/mutex.h>
#include <pico/rand.h>
#include <sys/time.h>
#include <lwip/dns.h>
#include <lwip/udp.h>
#include "logger_network.h"
#include "logger_upload.h"
#include "logger_sd.h"
#include "sntp_packet.h"
#include "wifi_schedule.h"
#include "secrets.h"

#if !defined(PICO_CYW43_SUPPORTED)
#error Select rp2040:rp2040:rpipicow
#endif

namespace {
constexpr uint64_t JOIN_US = 20000000ULL;
constexpr uint64_t BACKOFF_US = 30000000ULL;
constexpr uint64_t DNS_US = 10000000ULL;
constexpr uint64_t REPLY_US = 3000000ULL;
constexpr uint64_t RESYNC_US = 3600000000ULL;
const char *const TIME_SERVERS[] = {"pool.ntp.org", "time.nist.gov"};

// Core 6.1.0's WiFi.beginNoBlock() still calls CYW43::begin(), which waits
// for association (including an unbounded tail). Override only that adapter
// entry point. Keep the core's netif/DHCP/frame handling and radio firmware.
// All radio calls, including these control transactions, stay on core 0.
class AsyncRadio : public CYW43 {
public:
    using CYW43::CYW43;
    bool begin(const uint8_t *, struct netif *iface) {
        _self = &cyw43_state;
        _itf = CYW43_ITF_STA;
        _netif = iface;
        cyw43_arch_enable_sta_mode();
        cyw43_wifi_get_mac(_self, _itf, iface->hwaddr);
        const size_t passLength = strlen(WIFI_PASS);
        int rc = cyw43_wifi_join(_self, strlen(WIFI_SSID),
            reinterpret_cast<const uint8_t *>(WIFI_SSID), passLength,
            reinterpret_cast<const uint8_t *>(WIFI_PASS),
            passLength ? CYW43_AUTH_WPA2_AES_PSK : CYW43_AUTH_OPEN,
            nullptr, CYW43_CHANNEL_NONE);
        if (rc) {
            CYW43::end();
            return false;
        }
        return true;
    }
};
LwipIntfDev<AsyncRadio> radio;
enum class WifiState { Down, Joining, Up };
enum class TimeState { Idle, Resolving, Waiting };

struct Snapshot {
    WifiState wifi = WifiState::Down;
    const char *reason = "starting";
    uint8_t ip[4] = {};
    int32_t rssi = 0;
    uint64_t since = 0;
    uint64_t retryAt = 0;
    bool synced = false;
    uint64_t epochUs = 0;
    uint64_t syncAt = 0;
    uint32_t wifiRevision = 0;
    uint32_t timeRevision = 0;
    logger_wifi::Phase schedule = logger_wifi::Phase::Unknown;
    logger_wifi::Reason scheduleReason = logger_wifi::Reason::UnknownIgn;
    // Where the clock came from, so a timestamp in the record is never
    // anonymous. The host's clock is as good as SNTP when the host says it is
    // synchronised -- and much worse when it is not -- so which one set it is
    // worth carrying.
    bool fromHost = false;
};
auto_init_mutex(mailboxMutex);
Snapshot published, state;
bool counterReady = false, wantedLed = false;
bool ignKnown = false, ignOn = false;
logger_wifi::Schedule schedule;
// Core 1 writes these under mailboxMutex; core 0 consumes and clears them.
// Zero means "nothing asked for": a real request can never be zero, because
// adoptHostTime() is only reached by a frame that already passed a range check
// starting in 2026.
uint64_t hostTimeMs = 0, hostTimeAt = 0;
bool radioStarted = false;
uint64_t joinAt = 0, pollAt = 0, statusAt = 0, ledAt = 0;
TimeState timeState = TimeState::Idle;
uint64_t ntpDue = 0, timeDeadline = 0, sentAt = 0;
uint32_t dnsGeneration = 0;
unsigned serverIndex = 0;
struct udp_pcb *ntpSocket = nullptr;
ip_addr_t serverAddress;
uint8_t requestNonce[8];
// These fields are accessed only with LWIPMutex held (including callbacks,
// which already execute under the core's lwIP lock).
bool dnsDone = false, dnsOk = false, replyReady = false;
uint64_t replyEpochUs = 0, replyAt = 0;

void publish() {
    mutex_enter_blocking(&mailboxMutex);
    published = state;
    mutex_exit(&mailboxMutex);
}

Snapshot snapshot() {
    // Core 1 must never wait for network work, even during a failed join.
    static Snapshot cached;
    if (mutex_try_enter(&mailboxMutex, nullptr)) {
        cached = published;
        mutex_exit(&mailboxMutex);
    }
    return cached;
}

void closeTimeAttempt() {
    LWIPMutex lock;
    ++dnsGeneration; // Ignore a DNS callback arriving after cancellation.
    if (ntpSocket) udp_remove(ntpSocket);
    ntpSocket = nullptr;
    timeState = TimeState::Idle;
    dnsDone = replyReady = false;
}

void timeFailed(uint64_t now) {
    closeTimeAttempt();
    ntpDue = now + BACKOFF_US;
    serverIndex = (serverIndex + 1) % 2;
}

void dnsFound(const char *, const ip_addr_t *address, void *arg) {
    if (uint32_t(reinterpret_cast<uintptr_t>(arg)) != dnsGeneration ||
        timeState != TimeState::Resolving) return;
    dnsOk = address && !ip_addr_isany(address);
    if (dnsOk) serverAddress = *address;
    dnsDone = true;
}

void timeReceived(void *, struct udp_pcb *, struct pbuf *p,
                  const ip_addr_t *address, uint16_t port) {
    if (!p) return;
    uint8_t bytes[48];
    const uint64_t now = time_us_64();
    if (timeState == TimeState::Waiting && !replyReady && port == 123 &&
        ip_addr_eq(address, &serverAddress) && p->tot_len == sizeof(bytes) &&
        pbuf_copy_partial(p, bytes, sizeof(bytes), 0) == sizeof(bytes) &&
        logger_sntp::decode(bytes, sizeof(bytes), requestNonce,
                            now - sentAt, replyEpochUs)) {
        replyAt = now;
        replyReady = true;
    }
    pbuf_free(p);
}

void pollTime(uint64_t now) {
    LWIPMutex lock;
    if (timeState == TimeState::Idle) {
        if (now < ntpDue) return;
        timeState = TimeState::Resolving;
        dnsDone = dnsOk = false;
        ++dnsGeneration;
        timeDeadline = now + DNS_US;
        err_t rc = dns_gethostbyname(TIME_SERVERS[serverIndex], &serverAddress,
            dnsFound, reinterpret_cast<void *>(uintptr_t(dnsGeneration)));
        if (rc == ERR_OK) dnsDone = dnsOk = true;
        else if (rc != ERR_INPROGRESS) timeFailed(now);
        return;
    }
    if (timeState == TimeState::Resolving) {
        if (!dnsDone) {
            if (now >= timeDeadline) timeFailed(now);
            return;
        }
        if (!dnsOk) { timeFailed(now); return; }
        ntpSocket = udp_new();
        if (!ntpSocket || udp_bind(ntpSocket, IP_ADDR_ANY, 0) != ERR_OK) {
            timeFailed(now);
            return;
        }
        udp_recv(ntpSocket, timeReceived, nullptr);
        uint8_t bytes[48] = {};
        bytes[0] = 0x23; // LI=0, version 4, client mode.
        const uint64_t nonce = get_rand_64();
        memcpy(requestNonce, &nonce, sizeof(nonce));
        memcpy(bytes + 40, requestNonce, sizeof(requestNonce));
        struct pbuf *packet = pbuf_alloc(PBUF_TRANSPORT, sizeof(bytes), PBUF_RAM);
        if (!packet) { timeFailed(now); return; }
        pbuf_take(packet, bytes, sizeof(bytes));
        sentAt = time_us_64();
        timeState = TimeState::Waiting;
        timeDeadline = sentAt + REPLY_US;
        err_t rc = udp_sendto(ntpSocket, packet, &serverAddress, 123);
        pbuf_free(packet);
        if (rc != ERR_OK) timeFailed(time_us_64());
        return;
    }
    if (replyReady) {
        state.synced = true;
        state.epochUs = replyEpochUs;
        state.syncAt = replyAt;
        state.fromHost = false;
        const uint64_t currentUs = replyEpochUs + time_us_64() - replyAt;
        struct timeval tv;
        tv.tv_sec = currentUs / 1000000ULL;
        tv.tv_usec = currentUs % 1000000ULL;
        settimeofday(&tv, nullptr);
        ++state.timeRevision;
        closeTimeAttempt();
        ntpDue = now + RESYNC_US;
        publish();
    } else if (now >= timeDeadline) timeFailed(now);
}

/* Adopt a clock the host handed over. CORE 0.
 *
 * Deliberately the same arithmetic as the SNTP accept path above, including
 * settimeofday() being given the time as of NOW rather than as of the reply:
 * `epochUs` and `syncAt` are a pair, and every reader -- networkPrintTime(),
 * nameFor(), renameWhenClockArrives() -- already knows how to age that pair
 * forward. Nothing downstream needs to care which source filled it in.
 *
 * It does NOT refuse to overwrite an SNTP sync. Both sources are trusted or
 * neither is, and the host only speaks when its own NTP says it is
 * synchronised; a later SNTP reply overwrites this just as freely. What must
 * never happen is a clock being set from an UNTRUSTED source, and that is
 * enforced at both ends -- vssrec checks NTPSynchronized before it sends, and
 * applyHostTime() range-checks the frame before it gets here. */
void adoptHostTime(uint64_t epochMs, uint64_t arrivedAt) {
    state.synced = true;
    state.epochUs = epochMs * 1000ULL;
    state.syncAt = arrivedAt;
    state.fromHost = true;
    const uint64_t currentUs = state.epochUs + time_us_64() - arrivedAt;
    struct timeval tv;
    tv.tv_sec = currentUs / 1000000ULL;
    tv.tv_usec = currentUs % 1000000ULL;
    settimeofday(&tv, nullptr);
    ++state.timeRevision;
    publish();
}

void wifiDown(const char *reason) {
    closeTimeAttempt();
    uploadDisconnect();
    if (radioStarted) radio.end();
    // Core 6.1.0's CYW43::end only leaves the AP; disable station mode too.
    // Keep the driver alive for its GPIO/LED. This is not whole-chip power-off.
    {
        LWIPMutex lock;
        if (cyw43_state.itf_state & (1 << CYW43_ITF_STA)) {
            cyw43_wifi_pm(&cyw43_state, CYW43_DEFAULT_PM);
            cyw43_arch_disable_sta_mode();
        }
    }
    radioStarted = false;
    state.wifi = WifiState::Down;
    state.reason = reason;
    state.retryAt = time_us_64() + BACKOFF_US;
    ++state.wifiRevision;
    publish();
}

void pollWifi(uint64_t now) {
    if (state.wifi == WifiState::Down) {
        if (now < state.retryAt) return;
        state.wifi = WifiState::Joining;
        state.reason = "joining";
        joinAt = now;
        ++state.wifiRevision;
        publish();
        radioStarted = radio.begin();
        if (!radioStarted) {
            // LwipIntfDev may have removed its netif after a DHCP allocation
            // failure without calling RawDev::end(). Detach the radio too.
            radio.CYW43::end();
            wifiDown("init-failed");
            return;
        }
        cyw43_wifi_pm(&cyw43_state, 0xA11140); // Match the core's noLowPowerMode.
        return;
    }
    int link = cyw43_wifi_link_status(&cyw43_state, CYW43_ITF_STA);
    IPAddress ip = radio.localIP();
    if (link == CYW43_LINK_JOIN && radio.connected() && ip.isSet()) {
        if (state.wifi != WifiState::Up) {
            state.wifi = WifiState::Up;
            state.since = now;
            ++state.wifiRevision;
            ntpDue = now;
            statusAt = 0;
        }
        if (now >= statusAt) {
            for (unsigned i = 0; i < 4; ++i) state.ip[i] = ip[i];
            if (cyw43_wifi_get_rssi(&cyw43_state, &state.rssi)) state.rssi = 0;
            publish();
            statusAt = now + 1000000ULL;
        }
    } else if (state.wifi == WifiState::Up || link < 0 || now - joinAt >= JOIN_US) {
        const char *reason = link == CYW43_LINK_NONET ? "no-ap" :
            link == CYW43_LINK_BADAUTH ? "auth" :
            link == CYW43_LINK_FAIL ? "join-failed" :
            state.wifi == WifiState::Up ? "link-lost" : "join-timeout";
        wifiDown(reason);
    }
}
} // namespace

void networkSetup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);
    publish();
}

void networkLoop() {
    if (!powerBackgroundAllowed()) {
        uploadDisconnect();
        return;
    }
    bool ready, led, known, on;
    uint64_t askedMs = 0, askedAt = 0;
    mutex_enter_blocking(&mailboxMutex);
    ready = counterReady;
    led = wantedLed;
    known = ignKnown; on = ignOn;
    askedMs = hostTimeMs;
    askedAt = hostTimeAt;
    hostTimeMs = hostTimeAt = 0;        // consumed: adopt it exactly once
    mutex_exit(&mailboxMutex);
    // Drained BEFORE the counterReady gate. The clock is worth having whether
    // or not the radio ever comes up -- on a boot away from any known AP the
    // host is the only source there will be, and that is the whole point of
    // this path.
    if (askedMs) adoptHostTime(askedMs, askedAt);
    if (!ready) return;
    const uint64_t now = time_us_64();
    if (now >= pollAt) {
        pollAt = now + 100000ULL;
        const bool wasEnabled = schedule.enabled();
        schedule.step(now / 1000, {known, on, uploadProgress(), uploadCaughtUp(), state.timeRevision});
        if (state.schedule != schedule.phase() || state.scheduleReason != schedule.reason()) {
            state.schedule = schedule.phase();
            state.scheduleReason = schedule.reason();
            ++state.wifiRevision;
            if (wasEnabled && !schedule.enabled()) wifiDown(logger_wifi::name(schedule.reason()));
            if (!schedule.enabled()) { state.reason = logger_wifi::name(schedule.reason()); state.retryAt = 0; }
            if (!wasEnabled && schedule.enabled()) {
                uploadBeginWindow(); state.retryAt = 0;
            }
            publish();
        }
        if (schedule.enabled()) {
            pollWifi(now);
            if (state.wifi == WifiState::Up) pollTime(time_us_64());
        }
    }
    if (schedule.enabled()) uploadLoop(state.wifi == WifiState::Up);
    if (now >= ledAt) {
        ledAt = now + 1000000ULL;
        digitalWrite(LED_BUILTIN, led ? HIGH : LOW);
    }
}

void networkSetHostTime(uint64_t epochMs) {
    const uint64_t at = time_us_64();
    mutex_enter_blocking(&mailboxMutex);
    hostTimeMs = epochMs;
    hostTimeAt = at;
    mutex_exit(&mailboxMutex);
}

void networkCounterReady() {
    mutex_enter_blocking(&mailboxMutex);
    counterReady = true;
    mutex_exit(&mailboxMutex);
}

void networkSetLed(bool moving) {
    if (mutex_try_enter(&mailboxMutex, nullptr)) {
        wantedLed = moving;
        mutex_exit(&mailboxMutex);
    }
}

void networkSetIgn(bool on) {
    if (mutex_try_enter(&mailboxMutex, nullptr)) {
        ignKnown = true; ignOn = on;
        mutex_exit(&mailboxMutex);
    }
}

void networkPrintWifi() {
    const Snapshot s = snapshot();
    const uint64_t now = time_us_64();
    char ssid[33];
    // SSIDs are untrusted display text: never permit a newline or CSV comma
    // to turn a status note into another row. Association uses the real SSID.
    size_t i = 0;
    for (; i < sizeof(ssid) - 1 && WIFI_SSID[i]; ++i) {
        const uint8_t c = WIFI_SSID[i];
        ssid[i] = c >= 33 && c <= 126 && c != ',' ? char(c) : '_';
    }
    ssid[i] = 0;
    char note[128];
    if (s.wifi == WifiState::Up) {
        snprintf(note, sizeof(note),
            "# WIFI state=up ssid=%s ip=%u.%u.%u.%u rssi=%ld since=%llus",
            ssid, s.ip[0], s.ip[1], s.ip[2], s.ip[3], long(s.rssi),
            (now - s.since) / 1000000ULL);
    } else {
        snprintf(note, sizeof(note),
            "# WIFI state=%s ssid=%s reason=%s retry_in=%llus",
            s.schedule != logger_wifi::Phase::Window ? "off" :
                s.wifi == WifiState::Joining ? "joining" : "down", ssid, s.reason,
            s.retryAt > now ? (s.retryAt - now + 999999ULL) / 1000000ULL : 0ULL);
    }
    Out.println(note);
    // Separate bounded note: OutTee has a 160-byte line buffer.
    snprintf(note, sizeof(note), "# WIFI_POLICY state=%s reason=%s",
             logger_wifi::name(s.schedule), logger_wifi::name(s.scheduleReason));
    Out.println(note);
}

void networkPrintTime() {
    const Snapshot s = snapshot();
    if (!s.synced) {
        Out.println(F("# TIME unset src=none synced=0"));
        return;
    }
    const uint64_t ageUs = time_us_64() - s.syncAt;
    const time_t epoch = (s.epochUs + ageUs) / 1000000ULL;
    struct tm utc;
    gmtime_r(&epoch, &utc);
    char stamp[24], note[96];
    strftime(stamp, sizeof(stamp), "%Y-%m-%dT%H:%M:%SZ", &utc);
    snprintf(note, sizeof(note), "# TIME %s src=%s synced=1 age=%llus",
             stamp, s.fromHost ? "host" : "sntp", ageUs / 1000000ULL);
    Out.println(note);
}

bool networkWifiChanged() {
    static uint32_t seen = 0;
    const uint32_t now = snapshot().wifiRevision;
    if (now == seen) return false;
    seen = now;
    return true;
}

bool networkTimeChanged() {
    static uint32_t seen = 0;
    const uint32_t now = snapshot().timeRevision;
    if (now == seen) return false;
    seen = now;
    return true;
}

bool networkClockTrusted() {
    return state.synced;
}
