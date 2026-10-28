#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

namespace logger_upload {
constexpr size_t CHUNK = 512, REQUEST = 1280, RESPONSE = 1536;
constexpr uint64_t DEADLINE_MS = 8000, RETRY_MS = 30000, MAX_RETRY_MS = 300000;
constexpr uint32_t VISIT_BYTES = 65536;
struct File {
    char path[65] = {}, name[65] = {};
    uint32_t bytes = 0, generation = 0;
    bool closed = false, active = false;
};
struct Reply { unsigned status = 0; uint32_t bytes = 0; bool complete = false; };
// All wire identifiers are ASCII tokens; no query or JSON escaping is needed.
inline bool token(const char *s, size_t max) {
    size_t n = 0;
    for (; s[n]; ++n) {
        const unsigned char c = s[n];
        if (n >= max || !((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
            (c >= '0' && c <= '9') || c == '_' || c == '.' || c == '-')) return false;
    }
    return n && strcmp(s, ".") && strcmp(s, "..");
}
inline bool decimal(const char *&p, uint32_t &n) {
    if (*p < '0' || *p > '9') return false;
    n = 0;
    do {
        unsigned d = unsigned(*p++ - '0');
        if (n > (UINT32_MAX - d) / 10) return false;
        n = n * 10 + d;
    } while (*p >= '0' && *p <= '9');
    return true;
}
inline void space(const char *&p) { while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') ++p; }
inline bool string(const char *&p, char *s, size_t cap) {
    if (*p++ != '"') return false;
    size_t n = 0;
    while (*p && *p != '"') {
        if (n + 1 >= cap || *p == '\\' || (unsigned char)*p < 32) return false;
        s[n++] = *p++;
    }
    if (*p != '"') return false;
    ++p; s[n] = 0; return true;
}
// Strict, bounded flat JSON response. Fail closed on mismatched file IDs,
// duplicate keys, overflow, unsupported encoding or truncated bodies.
inline bool body(const char *p, const char *name, Reply &r) {
    bool file = false, bytes = false, complete = false;
    space(p); if (*p++ != '{') return false;
    for (unsigned fields = 0; fields < 3; ++fields) {
        char key[16], value[65];
        space(p); if (!string(p, key, sizeof(key))) return false;
        space(p); if (*p++ != ':') return false; space(p);
        if (!strcmp(key, "file")) {
            if (file || !string(p, value, sizeof(value)) || strcmp(value, name)) return false;
            file = true;
        } else if (!strcmp(key, "bytes")) {
            if (bytes || !decimal(p, r.bytes)) return false;
            bytes = true;
        } else if (!strcmp(key, "complete")) {
            if (complete) return false;
            if (!strncmp(p, "true", 4)) { r.complete = true; p += 4; }
            else if (!strncmp(p, "false", 5)) { r.complete = false; p += 5; }
            else return false;
            complete = true;
        } else return false;
        space(p);
        if (*p == '}') { ++p; space(p); return !*p && file && bytes; }
        if (*p++ != ',') return false;
    }
    return false;
}
// 0 = incomplete, 1 = valid, -1 = invalid. Input is NUL terminated at len.
inline int response(char *data, size_t len, const char *name, Reply &r) {
    if (strlen(data) != len) return -1;
    const char *end = strstr(data, "\r\n\r\n");
    if (!end) return len >= RESPONSE - 1 ? -1 : 0;
    if (strncmp(data, "HTTP/1.0 ", 9) && strncmp(data, "HTTP/1.1 ", 9)) return -1;
    if (len < 13 || data[12] != ' ') return -1;
    if (!strncmp(data + 9, "200", 3)) r.status = 200;
    else if (!strncmp(data + 9, "409", 3)) r.status = 409;
    else return -1;
    const char *p = strstr(data, "\r\n");
    if (!p || p > end) return -1;
    bool haveLength = false; uint32_t length = 0;
    while (p < end) {
        p += 2;
        const char *q = strstr(p, "\r\n");
        if (!q) return -1;
        char key[64]; size_t k = 0;
        while (p < q && *p != ':' && k + 1 < sizeof(key)) key[k++] = char(tolower((unsigned char)*p++));
        key[k] = 0;
        if (p == q || *p++ != ':') return -1;
        while (*p == ' ' || *p == '\t') ++p;
        if (!strcmp(key, "content-length")) {
            if (haveLength || !decimal(p, length)) return -1;
            while (*p == ' ' || *p == '\t') ++p;
            if (p != q) return -1;
            haveLength = true;
        } else if (!strcmp(key, "transfer-encoding")) return -1;
        p = q;
    }
    const size_t head = size_t(end + 4 - data);
    if (!haveLength || length >= RESPONSE || head + length >= RESPONSE) return -1;
    if (len < head + length) return 0;
    if (len != head + length) return -1;
    return body(end + 4, name, r) ? 1 : -1;
}

// Shared production state machine. IO separates SD and nonblocking transport
// so the same code can be exercised against real HTTP on a Linux host.
// next(): 0=one scan step/no item, 1=item, 2=end, -1=storage failure.
// poll(): 0=pending, 1=response complete, -1=failed.
template<class IO> class Client {
public:
    explicit Client(IO &io) : io(io) {}
    uint64_t progress() const { return progress_; }
    bool caughtUp() const { return caughtUp_; }
    // Abort before netif removal. Directory rewind waits for storage priority;
    // the next window must not inherit a partial scan, socket or retry deadline.
    void restart() {
        io.stop(); phase = Select; due = 0; backoff = RETRY_MS;
        caughtUp_ = false; sweepClean = true; sweepSawFile = false;
        rewindPending = true;
    }
    void step(uint64_t now) {
        if (!io.networkUp()) {
            caughtUp_ = false; sweepClean = false;
            if (phase != Select) fail(now);
            return;
        }
        if (now < due) return;
        if (phase == Wait) {
            if (!io.valid(file) || now >= deadline) { fail(now); return; }
            Reply reply;
            const int rc = io.poll(file.name, reply);
            if (!rc) return;
            io.stop();
            if (rc < 0 || reply.bytes > file.bytes) { fail(now); return; }
            // A sealed prefix can never be extended. Treat that disagreement
            // as an error instead of spinning on identical 409 offsets.
            if (reply.complete && (!file.closed || reply.bytes != file.bytes)) { fail(now); return; }
            if (action == Complete) {
                if (reply.status == 200 && reply.complete && reply.bytes == file.bytes) {
                    ++progress_; finish();
                }
                else if (reply.status == 409 && reply.bytes < file.bytes) { offset = reply.bytes; phase = Send; }
                else fail(now); // Missing /complete never implies success.
                return;
            }
            if (action == Append && reply.status == 200 && reply.bytes != offset + count) { fail(now); return; }
            if (action == Offset && reply.status != 200) { fail(now); return; }
            if (action == Append && reply.status == 409 && reply.bytes == offset) { fail(now); return; }
            if (action == Append && reply.bytes > offset) ++progress_;
            offset = reply.bytes;
            backoff = RETRY_MS;
            // Already sealed is verification, not new upload progress.
            if (action == Offset && reply.complete) { finish(); return; }
            phase = Send;
            return;
        }
        // Storage gets priority on EVERY pass that may select/read/send data.
        if (!io.storageReady()) return;
        if (rewindPending) {
            io.rewind(); rewindPending = false;
            sweepClean = true; sweepSawFile = false;
            return;
        }
        if (phase == Select) {
            const int rc = io.next(file);
            if (rc < 0) { fail(now); return; }
            if (rc == 2) {
                caughtUp_ = sweepClean && sweepSawFile;
                sweepClean = true; sweepSawFile = false;
                io.rewind(); due = now + RETRY_MS; return;
            }
            if (!rc) return;
            caughtUp_ = false; sweepSawFile = true;
            if (!token(file.name, 64)) { fail(now); return; }
            budget = VISIT_BYTES;
            action = Offset; count = 0; offset = 0;
        } else {
            if (!io.valid(file)) { fail(now); return; }
            if (offset == file.bytes) {
                if (!file.closed) { finish(); return; }
                action = Complete; count = 0;
            } else {
                if (!budget) { sweepClean = false; finish(); return; }
                action = Append;
                count = file.bytes - offset;
                if (count > CHUNK) count = CHUNK;
                if (io.read(file, offset, payload, count) != int(count)) { fail(now); return; }
                budget -= count;
            }
        }
        const char *endpoint = action == Offset ? "offset" : action == Append ? "append" : "complete";
        char suffix[40] = {};
        if (action != Offset) snprintf(suffix, sizeof(suffix), "&%s=%lu",
            action == Append ? "from" : "bytes", (unsigned long)(action == Append ? offset : file.bytes));
        const int n = snprintf(request, sizeof(request),
            "%s /v1/%s?unit=%s&file=%s%s HTTP/1.0\r\nHost: %s:%u\r\n"
            "Authorization: Bearer %s\r\nContent-Type: application/octet-stream\r\n"
            "Content-Length: %u\r\nConnection: close\r\n\r\n",
            action == Offset ? "GET" : "POST", endpoint, io.unit(), file.name,
            suffix, io.host(), io.port(), io.token(), unsigned(count));
        if (n < 0 || size_t(n) + count >= sizeof(request)) { fail(now); return; }
        memcpy(request + n, payload, count);
        if (!io.start(request, size_t(n) + count)) { fail(now); return; }
        deadline = now + DEADLINE_MS; phase = Wait;
    }
private:
    enum Phase { Select, Send, Wait } phase = Select;
    enum Action { Offset, Append, Complete } action = Offset;
    IO &io;
    File file;
    uint32_t offset = 0, budget = 0;
    size_t count = 0;
    uint64_t due = 0, deadline = 0, backoff = RETRY_MS;
    uint64_t progress_ = 0;
    bool caughtUp_ = false, sweepClean = true, sweepSawFile = false, rewindPending = false;
    char request[REQUEST], payload[CHUNK];
    void finish() { phase = Select; backoff = RETRY_MS; }
    void fail(uint64_t now) {
        caughtUp_ = false; sweepClean = false;
        io.stop(); phase = Select; due = now + backoff;
        backoff = backoff < MAX_RETRY_MS / 2 ? backoff * 2 : MAX_RETRY_MS;
    }
};
} // namespace logger_upload
