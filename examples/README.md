# Fixed Income consumer example

`fi_consumer.py` connects to `/ws/fi`, checks sequence numbers, timestamps, price/yield ranges, and upserts an in-memory **Security Master** keyed by `instrument_id` (CUSIP/ISIN from `fi_refdata.yaml`).

This is the post-receipt pattern: vendor ticks are not the master; they enrich it after quality checks. Holding Master and Transaction Master are out of scope for this vendor mock.
