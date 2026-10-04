# HTTP diagnostic service

`topazio_http.py` is a dependency-free development service. It binds to
`127.0.0.1` by default and exposes:

- `/healthz`: liveness JSON;
- `/status`: Core status JSON;
- `/metrics`: small Prometheus-compatible text sample.

It is not an authenticated production API. The QEMU lab binds it to the guest
network for smoke testing; a future target image must put authentication,
network policy, rate limits and TLS/SSH tunneling around any non-local
administration endpoint.
