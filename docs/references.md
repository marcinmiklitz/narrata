# References

This list maps research-derived ideas to their implementations in narrata.

## Implemented

- **[LLMTime]** Gruver et al., "Large Language Models Are Zero-Shot Time Series Forecasters", NeurIPS 2023. arXiv:2310.07820
  - Used in: `narrata.compression.digits` — digit-level tokenization for BPE-friendly numeric encoding.

- **[SAX]** Lin et al., "Experiencing SAX: A Novel Symbolic Representation of Time Series", DMKD 2007.
  - Used in: `narrata.analysis.symbolic` — SAX-style symbolic encoding (in-house fallback and tslearn backend).

- **[ASTRIDE]** Combettes et al., "An Adaptive Symbolization for Time Series", EUSIPCO 2024. arXiv:2302.04097
  - Used in: `narrata.analysis.symbolic` — adaptive change-point-based symbolization via ruptures.

## Libraries

- **[pandas-ta]** `pandas-ta-openbb` — Technical indicator computation (RSI, MACD, candlestick patterns). Optional backend for `narrata.analysis.indicators` and `narrata.analysis.patterns`.
- **[ruptures]** Truong et al., "Selective Review of Offline Change Point Detection Methods", Signal Processing 2020. Used for regime change-point detection and ASTRIDE segmentation.
- **[tslearn]** Tavenard et al., "tslearn: A Machine Learning Toolkit for Time Series Data", JMLR 2020. Used for SAX symbolization backend.
- **[toons]** TOON serialization format for token-efficient structured output.
