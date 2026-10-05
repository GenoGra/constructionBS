#!/usr/bin/env bash
#
# Normalize a POASTA GFA so its W-lines match the field convention used by the
# walk-based tools in this repo (Cactus / MinigraphCactus / ProgressiveCactus).
#
# POASTA emits walks as:   W  *  <hap>  <sample>#<hap>#<locus>  <start> <end> <walk>
# i.e. sample is "*" and the PanSN string lands in the seqid field, which is not
# GFA-1.1 conformant and breaks viewers. This rewrites each W-line to:
#                          W  <PREFIX>-<sample>  <hap>  <locus>  <start> <end> <walk>
# matching e.g. "W  C4-GRCh38  0  C4  ...".
#
# It also derives a `<base>_with_plines.gfa` where ONLY the reference sample is
# converted to a P-line (walk ">a>b<c" -> "a+,b+,c-"), every other sample staying
# a W-line, mirroring the *_with_plines.gfa files produced for the Cactus family.
#
# Usage:
#   utils/normalize_poasta_gfa.sh <canonical.gfa> <locus> <reference_sample>
#   e.g. utils/normalize_poasta_gfa.sh \
#          results/C4_TEST/POASTA/outputs/poasta_C4.gfa C4 C4-GRCh38
#
# The canonical GFA is normalized in place (a .orig backup is kept once).

set -euo pipefail

GFA="${1:?usage: normalize_poasta_gfa.sh <canonical.gfa> <locus> <reference_sample>}"
LOCUS="${2:?missing locus token, e.g. C4}"
REF_SAMPLE="${3:?missing reference sample name, e.g. C4-GRCh38}"

if [[ ! -s "$GFA" ]]; then
    echo "ERROR: GFA not found or empty: $GFA" >&2
    exit 1
fi

PREFIX="${LOCUS}-"
BASE="${GFA%.gfa}"
PLINES="${BASE}_with_plines.gfa"
TMP="${GFA}.tmp"

# Keep a one-time backup of the raw POASTA output.
if [[ ! -f "${GFA}.orig" ]]; then
    cp "$GFA" "${GFA}.orig"
fi

# 1) Normalize W-lines in place.
#    W * hap SAMPLE#HAP#LOCUS start end walk  ->  W PREFIX-SAMPLE HAP LOCUS start end walk
awk -v OFS='\t' -v prefix="$PREFIX" -v locus="$LOCUS" '
$1 != "W" { print; next }
{
    panSN = $4
    n = split(panSN, a, "#")
    if (n != 3) {
        print "ERROR: W seqid is not <sample>#<hap>#<locus>: " panSN > "/dev/stderr"
        exit 1
    }
    sample = a[1]
    hap    = a[2]
    $2 = prefix sample
    $3 = hap
    $4 = locus
    print
}
' "$GFA" > "$TMP"
mv "$TMP" "$GFA"

# 2) Derive *_with_plines.gfa: reference W -> P, everyone else unchanged.
awk -v OFS='\t' -v ref="$REF_SAMPLE" '
$1 == "W" && $2 == ref {
    walk = $7
    gsub(/>/, ",", walk)
    gsub(/</, ",-", walk)   # leading marker for reverse; cleaned below
    sub(/^,/, "", walk)
    n = split(walk, steps, ",")
    path = ""
    for (i = 1; i <= n; i++) {
        s = steps[i]
        if (s == "") continue
        if (s ~ /^-/) elem = substr(s, 2) "-"
        else          elem = s "+"
        path = path (path ? "," : "") elem
    }
    print "P", ref, path, "*"
    found = 1
    next
}
{ print }
END {
    if (!found) {
        print "[WARN] reference W-line not found for " ref > "/dev/stderr"
        exit 1
    }
}
' "$GFA" > "$PLINES"

echo "Normalized canonical: $GFA"
echo "Derived with_plines : $PLINES"
awk -F'\t' '/^P/{p++} /^W/{w++} END{print "with_plines counts -> P=" p+0 " W=" w+0}' "$PLINES"
