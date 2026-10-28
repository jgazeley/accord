#pragma once
#include "upload_protocol.h"

namespace logger_upload {
// Header only: never accept an identity from a later note or sample. Unknown
// legacy BOOT names are not unique across boots and must not be uploaded.
inline bool identity(const char *header, const char *path, const char *unit,
                     char *name, bool &sealable) {
    const char *end = strstr(header, "\n# log.end\n");
    if (strncmp(header, "# accord-log/1\n", 15) || !end) return false;
    char expected[64];
    snprintf(expected, sizeof(expected), "\n# log.unit chip=%s ", unit);
    const char *owner = strstr(header, expected);
    if (!owner || owner >= end) return false;
    const char *id = strstr(header, "\n# log.upload id=");
    sealable = false;
    if (id && id < end) {
        id += strlen("\n# log.upload id=");
        for (unsigned i = 0; i < 32; ++i)
            if (!((id[i] >= '0' && id[i] <= '9') || (id[i] >= 'a' && id[i] <= 'f'))) return false;
        if (strncmp(id + 32, " policy=create-only\n", 20)) return false;
        snprintf(name, 65, "U_%.32s.CSV", id);
        sealable = true;
        return true;
    }
    // Legacy dated files keep their previous wire identity. Completion remains
    // manual; only files bearing the new create-only promise can be sealed.
    const char *base = path[0] == '/' ? path + 1 : path;
    if (strlen(base) != 19 || base[8] != '_' || strcmp(base + 15, ".CSV")) return false;
    for (unsigned i = 0; i < 15; ++i) if (i != 8 && !isdigit((unsigned char)base[i])) return false;
    strcpy(name, base);
    return true;
}
} // namespace logger_upload
