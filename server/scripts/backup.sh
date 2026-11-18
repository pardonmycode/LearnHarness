#!/bin/sh
# PostgreSQL backups for LearnHarness (runs in the postgres:17 image, POSIX sh).
#
#   backup.sh          loop: one dump per day at BACKUP_TIME, then delete old dumps
#   backup.sh once     a single dump now (plus cleanup), e.g. "backup now"
#
# Settings (from .env): POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST,
# POSTGRES_PORT, BACKUP_TIME (HH:MM, container time zone TZ, default 02:30),
# BACKUP_KEEP_DAYS (default 14), BACKUP_DIR (default /backups).
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_TIME="${BACKUP_TIME:-02:30}"
BACKUP_KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
export PGHOST="${POSTGRES_HOST:-db}"
export PGPORT="${POSTGRES_PORT:-5432}"
export PGUSER="${POSTGRES_USER:?POSTGRES_USER fehlt}"
export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD fehlt}"
DB="${POSTGRES_DB:?POSTGRES_DB fehlt}"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') backup: $*"
}

backup_once() {
    mkdir -p "$BACKUP_DIR"
    target="$BACKUP_DIR/${DB}_$(date '+%Y-%m-%d_%H%M%S').dump"
    # Write to a temporary name first so a broken dump never looks like a valid one.
    if pg_dump -Fc --no-owner --file="$target.partial" "$DB"; then
        mv "$target.partial" "$target"
        log "ok $target ($(du -h "$target" | cut -f1))"
    else
        rm -f "$target.partial"
        log "FEHLER: pg_dump fehlgeschlagen"
        return 1
    fi
    # Retention: remove dumps older than BACKUP_KEEP_DAYS days (and stale partial files).
    find "$BACKUP_DIR" -maxdepth 1 -type f \( -name '*.dump' -o -name '*.dump.partial' \) \
        -mmin +$((BACKUP_KEEP_DAYS * 1440)) -print -exec rm -f {} \; | while read -r old; do
        log "geloescht $old"
    done
}

seconds_until_next_run() {
    now=$(date '+%s')
    next=$(date -d "today $BACKUP_TIME" '+%s')
    if [ "$next" -le "$now" ]; then
        next=$(date -d "tomorrow $BACKUP_TIME" '+%s')
    fi
    echo $((next - now))
}

if [ "${1:-}" = "once" ]; then
    backup_once
    exit $?
fi

log "gestartet: taeglich um $BACKUP_TIME, aufbewahren $BACKUP_KEEP_DAYS Tage, Ziel $BACKUP_DIR"
while :; do
    wait_seconds=$(seconds_until_next_run)
    log "naechste Sicherung in $wait_seconds s"
    sleep "$wait_seconds"
    # A failed dump is logged; the loop keeps running and tries again the next day.
    backup_once || true
done
