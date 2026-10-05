Local patches applied during Docker build for upstream Theseus releases.

- `v1.0.0-add-gfa-paths.patch`: adds `P`/`W` GFA export support for `theseus_msa`
  by treating the first FASTA entry as the reference path and the remaining
  entries as sample walks.
