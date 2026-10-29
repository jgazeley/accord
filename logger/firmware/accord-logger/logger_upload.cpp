#include "logger_power.h"
#include <Arduino.h>
#include <lwIP_CYW43.h>
#include <lwip/tcp.h>
#include <lwip/ip_addr.h>
#include "logger_upload.h"
#include "logger_sd.h"
#include "upload_protocol.h"
#include "secrets.h"

// Empty endpoint disables uploading until a private build is configured.
// Numeric LAN IPv4 avoids a second DNS state machine and any blocking resolver.
#ifndef UPLOAD_HOST
#define UPLOAD_HOST ""
#endif
#ifndef UPLOAD_PORT
#define UPLOAD_PORT 8086
#endif

namespace {
struct Transport {
    tcp_pcb *pcb = nullptr;
    bool connected = false, failed = false, eof = false;
    const char *request = nullptr;
    size_t requestBytes = 0, sent = 0, received = 0;
    char response[logger_upload::RESPONSE] = {};

    // Callbacks run under LWIPMutex. They only move bounded bytes or flags;
    // all SD and protocol work remains in the scheduler, outside this lock.
    static err_t connectedCallback(void *arg, tcp_pcb *, err_t error) {
        auto &t = *static_cast<Transport *>(arg);
        t.connected = error == ERR_OK;
        t.failed = error != ERR_OK;
        return ERR_OK;
    }
    static void errorCallback(void *arg, err_t) {
        auto &t = *static_cast<Transport *>(arg);
        t.pcb = nullptr; // lwIP already freed it
        t.failed = true;
    }
    static err_t receiveCallback(void *arg, tcp_pcb *pcb, pbuf *p, err_t error) {
        auto &t = *static_cast<Transport *>(arg);
        if (!p) { t.eof = true; return ERR_OK; }
        if (error != ERR_OK || p->tot_len >= sizeof(t.response) - t.received) {
            t.failed = true;
        } else {
            t.received += pbuf_copy_partial(p, t.response + t.received, p->tot_len, 0);
            t.response[t.received] = 0;
        }
        tcp_recved(pcb, p->tot_len);
        pbuf_free(p);
        return ERR_OK;
    }
    void stop() {
        LWIPMutex lock;
        if (pcb) {
            tcp_arg(pcb, nullptr); tcp_recv(pcb, nullptr); tcp_err(pcb, nullptr);
            // No pending buffers or close retry state survives a request.
            tcp_abort(pcb);
            pcb = nullptr;
        }
    }
    bool start(const char *bytes, size_t n) {
        LWIPMutex lock;
        stop();
        ip_addr_t address;
        if (!ipaddr_aton(UPLOAD_HOST, &address)) return false;
        pcb = tcp_new();
        if (!pcb) return false;
        connected = failed = eof = false;
        request = bytes; requestBytes = n; sent = received = 0; response[0] = 0;
        tcp_arg(pcb, this);
        tcp_err(pcb, errorCallback);
        tcp_recv(pcb, receiveCallback);
        if (tcp_connect(pcb, &address, UPLOAD_PORT, connectedCallback) != ERR_OK) {
            stop(); return false;
        }
        return true;
    }
    int poll(const char *name, logger_upload::Reply &reply) {
        LWIPMutex lock;
        if (failed || !pcb) return -1;
        if (connected && sent < requestBytes) {
            size_t n = requestBytes - sent;
            if (n > 256) n = 256;
            if (n > tcp_sndbuf(pcb)) n = tcp_sndbuf(pcb);
            if (n) {
                const err_t rc = tcp_write(pcb, request + sent, n, TCP_WRITE_FLAG_COPY);
                if (rc == ERR_OK) { sent += n; tcp_output(pcb); }
                else if (rc != ERR_MEM) return -1;
            }
            return 0;
        }
        const int rc = logger_upload::response(response, received, name, reply);
        return rc ? rc : eof ? -1 : 0;
    }
};
struct IO {
    bool up = false;
    Transport transport;
    bool networkUp() const { return up; }
    bool storageReady() const { return sdUploadReady(); }
    bool valid(const logger_upload::File &f) const { return sdUploadValid(f); }
    int next(logger_upload::File &f) { return sdUploadNext(f); }
    void rewind() { sdUploadRewind(); }
    int read(const logger_upload::File &f, uint32_t at, char *out, size_t n) { return sdUploadRead(f, at, out, n); }
    const char *unit() const { return rp2040.getChipID(); }
    const char *host() const { return UPLOAD_HOST; }
    unsigned port() const { return UPLOAD_PORT; }
    const char *token() const { return API_TOKEN; }
    bool start(const char *p, size_t n) { return powerBackgroundAllowed() && transport.start(p, n); }
    int poll(const char *name, logger_upload::Reply &r) { return transport.poll(name, r); }
    void stop() { transport.stop(); }
};
IO io;
logger_upload::Client<IO> client(io);
}
void uploadLoop(bool wifiUp) {
    if (!powerBackgroundAllowed()) { uploadDisconnect(); return; }
    if (!UPLOAD_HOST[0]) return;
    io.up = wifiUp;
    client.step(time_us_64() / 1000);
}
void uploadDisconnect() { io.up = false; client.restart(); }
void uploadBeginWindow() { client.restart(); }
uint64_t uploadProgress() { return client.progress(); }
bool uploadCaughtUp() { return UPLOAD_HOST[0] && client.caughtUp(); }
