# Governance and Limitations

- The risk score is ranking-oriented, not a calibrated probability of default.
- Cost analysis is normalized and does not represent realized financial profit.
- Customer-level exposure, loss, revenue, recovery, and credit limit information are unavailable.
- The weighted correction approximates broader non-default review workload under AMEX downsampling.
- Public repository files include masked samples and aggregate outputs only.
- This project supports manual review prioritization and monitoring.
- It is not an automatic adverse-action system.

Production deployment would require:

- shadow-mode validation,
- champion-challenger testing,
- calibration validation,
- drift monitoring,
- compliance review,
- fairness and bias checks,
- access control,
- audit logging.
