# CHAPTER FOUR: RESULTS AND DISCUSSION

## 4.2 Analysis of Marine Machinery Operation Data

### 4.2.1 Data Description

The dataset used in this study, `sealine_data_with_features.csv`, contains **2,007 operational sensor readings** collected from four marine machines aboard the vessel *Ikraam Sea Line*: two main engines (**ME1**, **ME2**) and two generators (**GEN1**, **GEN2**). Each record represents a single timestamped sensor reading and includes the following raw fields:

| Column | Description |
|---|---|
| `Voyage` | Voyage identifier for the reading |
| `Date`, `Time` | Timestamp of the reading |
| `Machine_Category` | "Engine" or "Generator" |
| `Machine_ID` | Specific machine identifier (ME1, ME2, GEN1, GEN2) |
| `Engine RPM` | Shaft/engine rotational speed |
| `Lub oil pressure` | Lubrication oil pressure |
| `Lub oil temperature` | Lubrication oil temperature |
| `Coolant temperature` | Engine coolant temperature |
| `Exhaust temperature` | Exhaust gas temperature (occasionally missing) |
| `Status` / `Status_label` | Ground-truth condition label: Normal (0) or Fault (1) |

In addition to the raw sensor readings, the dataset already contains five **rule-based fault flags** (`oil_pressure_fault`, `oil_temp_fault`, `coolant_temp_fault`, `exhaust_temp_fault`, `rpm_fault`), a derived `num_rules_triggered` count, and an `is_generator` binary indicator. These engineered features, together with the five raw sensor columns, form the 12-feature input space used throughout this study.

The class distribution of the target variable is imbalanced: **1,776 readings (88.5%) are labelled Normal** and **231 readings (11.5%) are labelled Fault**. This imbalance is characteristic of real-world condition-monitoring data, where fault events are inherently rarer than normal operation, and it directly motivated the use of class-weighting during model training (Sections 4.3.2 and 4.3.3).

### 4.2.2 Data Preprocessing

Several data quality issues were identified and addressed before the dataset could be used for model training:

1. **Inconsistent date formats.** The `Date` column mixed ISO format (`YYYY-MM-DD HH:MM:SS`) with day-first format (`DD/MM/YYYY`), and a small number of entries contained typographical errors in the year field (e.g. `18/10/2925`, `19/20/2025`, `25/10/20265`, `12/11/205`). A mixed-format parser (`pandas.to_datetime(..., format="mixed", dayfirst=True, errors="coerce")`) was used to parse every row individually rather than assuming a single format for the whole column. The **47 rows (2.3% of the dataset) whose dates remained unparseable** after this step were dropped, since their position in a machine's chronological sequence could not be determined reliably.

2. **Missing sensor values.** The `Exhaust temperature` column contained missing values for a subset of readings (flagged by an `exhaust_temp_missing` indicator in the source file), most commonly for generator readings. Missing values were filled with 0 prior to model training (`fillna(0)`), matching the fallback used later at prediction time. The corresponding `exhaust_temp_fault` rule was explicitly skipped (rather than evaluated against 0) whenever the raw reading was missing, to avoid manufacturing a false positive from an absent sensor value.

3. **Malformed machine identifiers.** Two rows carried a truncated `Machine_ID` of `"GEN"` and one row carried `"ME"` instead of a valid identifier (e.g. `GEN1`, `ME2`). Because these groups had fewer than the minimum ten readings required to construct an LSTM input sequence (Section 4.3.1), they were naturally excluded from sequence-based processing without requiring special-case handling.

4. **Outlier values.** Exploratory analysis (Section 4.2.3.1) revealed a small number of extreme outliers — for example a maximum recorded `Coolant temperature` of 699°C and a maximum `Engine RPM` of 6,670 — that are far outside physically plausible operating ranges for the machinery described. These outliers were retained in the dataset (rather than removed) since the scope of this study did not include a dedicated outlier-rejection stage, but their presence is noted here as a limitation of the source data and is revisited in the discussion of model performance (Section 4.4.4).

After preprocessing, **1,960 valid readings** remained for the Random Forest model (which operates on individual readings) and **1,921 readings** were eligible for sequence-based LSTM modelling (readings that additionally had at least nine prior chronological readings for the same machine).

### 4.2.3 Exploratory Data Analysis

#### 4.2.3.1 Descriptive Statistics

Table 4.1 summarises the descriptive statistics of the five continuous sensor variables.

**Table 4.1: Descriptive statistics of operational sensor variables**

| Variable | Mean | Std. Dev. | Min | Max |
|---|---|---|---|---|
| Engine RPM | 1326.34 | 376.35 | 100.00 | 6670.00 |
| Lub oil pressure | 5.21 | 4.19 | 3.10 | 91.50 |
| Lub oil temperature | 85.09 | 9.72 | 5.00 | 112.00 |
| Coolant temperature | 70.31 | 15.57 | 6.80 | 699.00 |
| Exhaust temperature | 380.13 | 132.48 | 355.00 | 3789.00 |

The maximum values recorded for Coolant temperature (699.00) and Exhaust temperature (3789.00) are well beyond realistic operating limits for marine diesel machinery, confirming the presence of the outliers noted in Section 4.2.2. The remaining variables show ranges broadly consistent with expected engine/generator operating conditions.

*(Figure 4.1: Descriptive statistics table, as rendered on the monitoring dashboard's "Descriptive Statistics" panel.)*

#### 4.2.3.2 Correlation Analysis

A Pearson correlation matrix was computed across the five sensor variables to examine linear relationships between them (Table 4.2).

**Table 4.2: Correlation matrix of operational sensor variables**

| | Engine RPM | Lub oil pressure | Lub oil temp. | Coolant temp. | Exhaust temp. |
|---|---|---|---|---|---|
| **Engine RPM** | 1.00 | 0.11 | 0.11 | 0.12 | 0.02 |
| **Lub oil pressure** | 0.11 | 1.00 | 0.15 | 0.07 | 0.01 |
| **Lub oil temperature** | 0.11 | 0.15 | 1.00 | 0.36 | 0.08 |
| **Coolant temperature** | 0.12 | 0.07 | 0.36 | 1.00 | 0.02 |
| **Exhaust temperature** | 0.02 | 0.01 | 0.08 | 0.02 | 1.00 |

The strongest inter-variable correlation observed is between **Lub oil temperature and Coolant temperature (r = 0.36)**, a weak-to-moderate positive relationship that is physically plausible, since both are influenced by the overall thermal load of the machine. All other pairwise correlations are weak (r < 0.2), indicating that the five sensor variables largely carry independent, non-redundant information — a desirable property for a multivariate classification model, as it suggests the model is not simply learning one variable as a proxy for another.

*(Figure 4.2: Correlation heatmap, as rendered on the monitoring dashboard's "Correlation Analysis" panel, using a diverging red–blue colour scale.)*

#### 4.2.3.3 Fault Condition Distribution

Figure 4.3 illustrates the overall class balance of the dataset: **1,776 Normal readings (88.5%)** against **231 Fault readings (11.5%)**. This confirms the class imbalance discussed in Section 4.2.1 and underlines why accuracy alone is an insufficient metric for evaluating the models developed in this study (see Section 4.4.4).

*(Figure 4.3: Fault Health Distribution donut chart, as rendered on the monitoring dashboard.)*

#### 4.2.3.4 Operational Parameter Visualization

To inspect how each sensor variable behaves over time and across machines, time-series line plots were produced for all five operational parameters (Engine RPM, Lubrication Oil Pressure, Lubrication Oil Temperature, Coolant Temperature, and Exhaust Gas Temperature). These plots were generated dynamically on the developed monitoring dashboard whenever a batch of readings is uploaded, using the reading's row order (or its recorded Date/Time, when available) as the horizontal axis.

Visual inspection of these trends was instrumental in identifying the data quality issues discussed in Section 4.2.2 — specifically, the sudden, physically implausible spikes in Coolant and Exhaust temperature that alerted the researcher to the presence of outliers before model training began.

*(Figure 4.4: Operational Parameters trend charts, as rendered on the monitoring dashboard's "Operational Parameters" panel.)*

---

## 4.3 Application of Hybrid Random Forest and LSTM Model

### 4.3.1 Data Preparation

**Feature selection.** Both models were trained on the same 12-feature input vector, engineered directly from each raw reading:

1. Engine RPM
2. Lub oil pressure
3. Lub oil temperature
4. Coolant temperature
5. Exhaust temperature
6. `is_generator` (1 if the machine is a Generator, 0 if an Engine)
7. `oil_pressure_fault` (1 if Lub oil pressure > 6.5 or < 2.5)
8. `oil_temp_fault` (1 if Lub oil temperature > 100 or < 50)
9. `coolant_temp_fault` (1 if Coolant temperature > 85 or < 60)
10. `exhaust_temp_fault` (1 if Exhaust temperature > 400; the check is skipped when the reading is missing)
11. `rpm_fault` (1 if Engine RPM > 1700 for an Engine, or > 1600 for a Generator)
12. `num_rules_triggered` (the sum of features 7–11)

This combination of raw sensor values and rule-derived flags gives both models access to both the continuous magnitude of each reading and an explicit, human-interpretable signal of threshold violation.

**Training and testing split.** An 80/20 train-test split was used for both models, with `random_state=42` fixed for reproducibility and stratification applied on the target label to preserve the 88.5%/11.5% class ratio in both partitions. For the head-to-head comparison of Random Forest, LSTM, and the Hybrid model (Section 4.4), a single shared test set of **385 readings** — drawn only from the 1,921 readings eligible for both models — was used, so that all three models were evaluated on identically the same held-out data.

**Normalization/scaling.** Random Forest, being a tree-based ensemble, does not require feature scaling and was trained directly on the raw feature values. The LSTM model, however, is sensitive to input scale, so all 12 features were scaled using a `MinMaxScaler` fitted **only on the training partition** (to avoid information leakage from the test set) before being applied to both the training and test sequences.

**Label encoding.** The target variable (`Status_label`) and the `is_generator` indicator were already represented as binary integers (0/1) in the source dataset, so no additional categorical encoding step was required. The `Machine_Category` string field ("Engine"/"Generator") was mapped to the binary `is_generator` flag for use as a model feature.

### 4.3.2 Random Forest Model Development

A `RandomForestClassifier` (scikit-learn) was selected as the first component of the hybrid system because of its strong baseline performance on structured/tabular data and its resistance to overfitting on the engineered rule-flag features.

**Model configuration:**
- `n_estimators = 200` (200 decision trees)
- `class_weight = "balanced"` (to compensate for the 88.5%/11.5% class imbalance)
- `random_state = 42` (for reproducibility)

**Training.** The model was fitted on the 80% training partition using the 12-feature vector described in Section 4.3.1. Each of the 200 trees is trained on a bootstrap-resampled subset of the training data, and the final prediction is obtained by aggregating the votes of all 200 trees.

**Output.** For a given reading, the Random Forest produces both a binary class prediction (Normal/Fault) and a continuous **fault probability**, computed as the proportion of the 200 trees that voted "Fault". This probability is thresholded at 0.5 to produce the final classification, and is also exposed directly to the end user through the developed monitoring dashboard.

### 4.3.3 LSTM Model Development

The second component of the hybrid system is a Long Short-Term Memory (LSTM) recurrent neural network, included to capture temporal trends across a sequence of readings that a single-reading model such as Random Forest cannot observe.

**Architecture:**

| Layer | Configuration | Purpose |
|---|---|---|
| LSTM | 64 units | Learns temporal patterns across the input sequence |
| Dropout | rate = 0.3 | Randomly deactivates 30% of connections during training to reduce overfitting |
| Dense | 16 units, ReLU activation | Non-linear feature combination |
| Dense | 1 unit, Sigmoid activation | Outputs a single probability of Fault, between 0 and 1 |

**Sequence construction.** For each machine (`Machine_ID`), readings were sorted chronologically and a sliding window of **10 consecutive readings** was used as one input sequence, with the target label taken from the 10th (most recent) reading in the window. This produced **1,921 sequences** across the four valid machine groups (ME1, ME2, GEN1, GEN2).

**Training configuration:**
- Optimizer: Adam
- Loss function: Binary cross-entropy
- `class_weight = "balanced"` (computed via `compute_class_weight`)
- Batch size: 32
- Maximum epochs: 30, with **Early Stopping** (monitoring validation loss, patience = 5 epochs, restoring the best-performing weights) — training stopped after approximately 10 epochs in practice.
- 20% of the training sequences were held out as a validation set during training (separate from the final test set).

### 4.3.4 Hybrid of RF and LSTM

The hybrid model combines the two independently trained models using a **simple probability-averaging ensemble**, rather than a jointly trained architecture. For a given machine at a given point in time:

1. The Random Forest produces a fault probability, `P_RF`, from the machine's single most recent reading.
2. The LSTM produces a fault probability, `P_LSTM`, from the sequence of the machine's last 10 readings.
3. The hybrid fault probability is computed as the arithmetic mean:

    **P_hybrid = (P_RF + P_LSTM) / 2**

4. The final classification is Fault if `P_hybrid ≥ 0.5`, otherwise Normal.

This averaging approach was chosen for its simplicity and interpretability: it requires no additional parameters to be learned, and the contribution of each model to the final decision is transparent and equal.

### 4.3.5 Model Training of Hybrid

It is important to clarify that **the hybrid model itself involves no separate training process.** The Random Forest and LSTM models are trained entirely independently, exactly as described in Sections 4.3.2 and 4.3.3, using their own respective feature/sequence representations. The "hybrid" step occurs only at **prediction (inference) time**, where the two models' already-computed probabilities are combined by simple averaging as described in Section 4.3.4. No additional model fitting, backpropagation, or parameter estimation is performed for the hybrid combination itself.

### 4.3.6 Fault Detection Result

On the shared 385-reading test set, the hybrid model achieved an accuracy of **99.74%**, with a **recall of 100%** on the Fault class — meaning every genuine fault reading in the test set was successfully flagged, with zero missed faults (false negatives). One false positive (a Normal reading incorrectly flagged as Fault) was recorded. Detailed performance figures, including a full breakdown against the Random Forest and LSTM models individually, are presented and discussed in Section 4.4.

---

## 4.4 Performance Evaluation of the Developed Hybrid RF and LSTM Model

### 4.4.1 Confusion Matrix

A confusion matrix summarises a classifier's predictions against the actual ground-truth labels in a 2×2 table:

| | Predicted Normal | Predicted Fault |
|---|---|---|
| **Actual Normal** | True Negative (TN) | False Positive (FP) |
| **Actual Fault** | False Negative (FN) | True Positive (TP) |

- **True Positive (TP):** A genuine Fault reading correctly identified as Fault.
- **True Negative (TN):** A genuine Normal reading correctly identified as Normal.
- **False Positive (FP):** A Normal reading incorrectly flagged as Fault (a "false alarm").
- **False Negative (FN):** A genuine Fault reading incorrectly classified as Normal (a **missed fault**).

In the context of marine machinery fault detection, the **False Negative is the most operationally dangerous error**, since it means a real developing fault goes undetected and could progress to equipment failure or a safety incident. A False Positive, while undesirable, only costs an unnecessary inspection. This asymmetry is why recall (Section 4.4.2) is treated as the most important single metric in this study, ahead of precision or raw accuracy.

**Table 4.3: Confusion matrices for all three models (test set, n = 385)**

| Model | TN | FP | FN | TP |
|---|---|---|---|---|
| Random Forest | 341 | 1 | 0 | 43 |
| LSTM | 246 | 96 | 25 | 18 |
| Hybrid (RF + LSTM average) | 341 | 1 | 0 | 43 |

### 4.4.2 Classification Performance Metrics

Four standard classification metrics were computed for each model:

- **Accuracy** = (TP + TN) / (TP + TN + FP + FN) — the overall proportion of correct predictions.
- **Precision** = TP / (TP + FP) — of all readings flagged as Fault, the proportion that were genuinely Fault.
- **Recall (Sensitivity)** = TP / (TP + FN) — of all genuine Fault readings, the proportion that were successfully detected.
- **F1-score** = 2 × (Precision × Recall) / (Precision + Recall) — the harmonic mean of precision and recall, balancing both.

**Table 4.4: Classification performance metrics (test set, n = 385)**

| Metric | Random Forest | LSTM | Hybrid |
|---|---|---|---|
| Accuracy | 99.74% | 68.57% | 99.74% |
| Precision (Fault) | 97.73% | 15.79% | 97.73% |
| Recall (Fault) | 100.00% | 41.86% | 100.00% |
| F1-score (Fault) | 98.85% | 22.93% | 98.85% |

### 4.4.3 ROC Curve and AUC

The Receiver Operating Characteristic (ROC) curve plots the True Positive Rate (Recall) against the False Positive Rate across all possible classification thresholds, and the Area Under the Curve (AUC) summarises this into a single value between 0 and 1 — with 1.0 representing a perfect classifier and 0.5 representing performance no better than random guessing.

**Table 4.5: ROC-AUC scores**

| Model | ROC-AUC |
|---|---|
| Random Forest | 0.9993 |
| LSTM | 0.7198 |
| Hybrid | 0.9976 |

The Random Forest and Hybrid models both achieve ROC-AUC scores above 0.997, indicating near-perfect separability between the Normal and Fault classes across virtually all decision thresholds. The LSTM's ROC-AUC of 0.7198 is markedly weaker, though still meaningfully better than random guessing (0.5), confirming that the LSTM has learned some genuine signal from the sequential data, even if its performance falls well short of the Random Forest.

*(Figure 4.5: ROC curve comparison of Random Forest, LSTM, and Hybrid models, generated by `ml/evaluate_all.py` and saved as `ml/models/roc_comparison.png`.)*

### 4.4.4 Model Performance Discussion

**Random Forest** achieved the strongest performance of the three models, with 99.74% accuracy and, most importantly, **100% recall** on the Fault class — no genuine fault in the test set was missed. Its precision of 97.73% indicates a low false-alarm rate (only one Normal reading was misclassified as Fault out of 385 test readings). This exceptional performance is best explained by the nature of the engineered features: the five rule-based fault flags are strong, near-deterministic indicators of the target label, since a reading that breaches a sensor threshold is very likely to have been labelled Fault in the source data using comparable threshold logic. Random Forest, as a model well suited to exploiting exactly this kind of structured, rule-like feature, was therefore able to learn the decision boundary almost perfectly. This should be read as a **caveat on the result**, not merely a triumph of the model: a large share of the model's apparent skill reflects the strength and directness of the engineered features rather than the discovery of subtle, non-obvious fault patterns. Any future deployment of this system on new machinery, sensor calibrations, or fault types not captured by the current five threshold rules would need to be validated afresh.

**LSTM** performed considerably worse (68.57% accuracy, 41.86% recall, 22.93% F1-score). Two factors plausibly explain this: first, only 1,921 training sequences were available — a small sample size for a neural network model, which typically benefits from substantially larger datasets to learn robust temporal patterns. Second, and more fundamentally, the faults in this dataset are almost all identifiable from a **single reading** (a threshold breach), which gives the LSTM's sequential/temporal view little additional information beyond what Random Forest already exploits from the same reading in isolation. The LSTM would be expected to add more value on a dataset containing gradually-developing faults, where the trend across several readings — rather than any single reading — is what signals an impending problem.

**Hybrid model.** Contrary to an initial expectation that averaging two models should always outperform either model individually, the Hybrid model's performance (99.74% accuracy, 100% recall) is **numerically identical** to that of the Random Forest alone, and its confusion matrix contains exactly the same single misclassification. This is a legitimate and instructive finding rather than a flaw in the implementation: simple averaging benefits most when two models make different, complementary kinds of errors on uncorrelated cases. Here, since the Random Forest is already near-perfect and the LSTM is comparatively weak, averaging the two probabilities together could not meaningfully improve on the Random Forest's result — at best, it could only "dilute" a small number of confident, correct Random Forest predictions with noisier LSTM output. This finding suggests that a simple 50/50 average is not, by itself, sufficient to guarantee an ensemble improvement when its constituent models differ greatly in individual strength, and that alternative ensembling strategies (e.g. a weighted average favouring the stronger model, or a learned meta-classifier) would be a natural direction for future improvement — provided the LSTM's own performance is also strengthened with more, and more temporally-informative, training data.

### 4.4.5 Summary of Model Performance

- **Random Forest** is the strongest individual model developed in this study, achieving 99.74% accuracy, 100% recall, and 97.73% precision on the held-out test set, driven largely by the strength of the rule-based engineered features.
- **LSTM** achieved materially weaker performance (68.57% accuracy, 41.86% recall) and is best understood, in this dataset, as a supplementary temporal-context model rather than a stand-alone fault detector.
- The **Hybrid model**, formed by averaging the two models' fault probabilities, matched the Random Forest's performance exactly (99.74% accuracy, 100% recall, 0 missed faults) but did not exceed it, because simple averaging cannot improve on an already near-perfect model when the second model in the ensemble is comparatively weak.
- Across all three models, **recall on the Fault class** was prioritised as the most operationally meaningful metric, since a missed fault (false negative) carries a far greater real-world cost than a false alarm. On this measure, both the Random Forest and the Hybrid model performed without error on the available test data (100% recall, 0 false negatives).
- These results should be interpreted with the dataset's characteristics in mind: fault labels in the source data are strongly tied to explicit sensor-threshold breaches, which favours a single-reading, rule-aware model such as Random Forest. Future work incorporating gradually-developing fault scenarios, a larger volume of sequential data, and more sophisticated ensembling techniques (weighted averaging or stacked meta-models) would provide a more demanding and realistic test of the LSTM and Hybrid components' true value.

---

## 4.6 Hypothesis Testing

This section evaluates the three research hypotheses stated in Section 1.4 against the empirical results presented in Sections 4.3 and 4.4. Because the hypotheses in this study concern the practical performance and comparative capability of trained classification models — rather than a comparison of population means or proportions across repeated independent samples — hypothesis testing here is conducted through **criterion-referenced evaluation**: each hypothesis is paired with an explicit, quantitative decision rule defined *before* the result is examined, and the hypothesis is accepted, partially accepted, or rejected according to whether the observed performance metrics (Section 4.4) satisfy that rule. This approach is standard practice for empirical machine learning research evaluated on a held-out test partition, and is used here in place of classical null-hypothesis significance testing (e.g. t-tests), which is not applicable to single-model, single-split classification outcomes of this kind.

### 4.6.1 Testing of Hypothesis One (H1)

**H1:** *Marine machinery operational data will significantly contribute to accurate fault detection.*

**Testing procedure.** H1 was tested by comparing the performance of the Random Forest model — trained directly on the marine machinery operational data described in Section 4.2 — against a **no-skill (majority-class) baseline**. The baseline classifier predicts "Normal" for every reading, without reference to any sensor value, and represents the accuracy attainable *without* using the operational data at all. If the data-driven model performs substantially and meaningfully better than this baseline, particularly in its ability to detect the minority Fault class, this provides evidence that the operational data carries genuine, exploitable information for fault detection.

**Decision rule.** H1 is **accepted** if the Random Forest model's accuracy and ROC-AUC both exceed the no-skill baseline by a wide margin, and in particular if it achieves meaningful recall on the Fault class (which the no-skill baseline, by construction, cannot).

**Table 4.6: Random Forest performance versus the no-skill baseline (test set, n = 385)**

| Metric | No-skill baseline (predict "Normal" always) | Random Forest (trained on operational data) |
|---|---|---|
| Accuracy | 88.51%¹ | 99.74% |
| Recall (Fault class) | 0.00% | 100.00% |
| ROC-AUC | 0.50 (no discriminative ability) | 0.9993 |

¹ Equal to the proportion of Normal readings in the dataset (1,776 / 2,007).

**Interpretation.** Although the no-skill baseline attains a superficially high accuracy of 88.51% — a direct consequence of the class imbalance discussed in Section 4.2.1 — it achieves **zero recall** on the Fault class, meaning it fails to detect a single genuine fault and is, in practice, useless as a fault-detection system. The Random Forest model, trained on the 12-feature operational-data representation, not only improves accuracy to 99.74% but achieves a Fault recall of 100% and a ROC-AUC of 0.9993 (compared to 0.50 for a non-discriminating classifier). This large, practically significant gap demonstrates that the marine machinery operational data — specifically, the raw sensor readings and their derived rule-based features — contains strong, exploitable information for distinguishing Normal from Fault operating conditions.

**Decision: H1 is ACCEPTED.**

### 4.6.2 Testing of Hypothesis Two (H2)

**H2:** *There will be significant improvement in fault detection when using the hybrid random forest-LSTM model in fault detection.*

**Testing procedure.** H2 was tested by comparing the Hybrid model's classification performance (Accuracy, Precision, Recall, F1-score, ROC-AUC) directly against **both** of its constituent standalone models — Random Forest and LSTM — on the identical shared test set (n = 385) used throughout Section 4.4.

**Decision rule.** H2 is **accepted** if the Hybrid model outperforms *both* standalone models on the majority of the five evaluation metrics; **partially accepted** if it demonstrates improvement over one standalone model but not the other; and **rejected** if it fails to improve over either.

**Table 4.7: Hybrid model performance relative to its constituent models (test set, n = 385)**

| Metric | LSTM alone | Random Forest alone | Hybrid (RF + LSTM) | Improvement vs. LSTM | Improvement vs. RF |
|---|---|---|---|---|---|
| Accuracy | 68.57% | 99.74% | 99.74% | +31.17 pp | 0.00 pp |
| Precision (Fault) | 15.79% | 97.73% | 97.73% | +81.94 pp | 0.00 pp |
| Recall (Fault) | 41.86% | 100.00% | 100.00% | +58.14 pp | 0.00 pp |
| F1-score (Fault) | 22.93% | 98.85% | 98.85% | +75.92 pp | 0.00 pp |
| ROC-AUC | 0.7198 | 0.9993 | 0.9976 | +0.2778 | −0.0017 |

**Interpretation.** Relative to the standalone LSTM model, the Hybrid model demonstrates a large and unambiguous improvement across every metric, most notably in Fault recall (+58.14 percentage points) and F1-score (+75.92 percentage points). This portion of the evidence strongly supports H2. However, relative to the standalone Random Forest model, the Hybrid model shows **no improvement whatsoever**: its accuracy, precision, recall, and F1-score are numerically identical to Random Forest's, and its ROC-AUC is marginally *lower* (0.9976 versus 0.9993). As discussed in Section 4.4.4, this outcome is attributable to the averaging mechanism used to construct the Hybrid model (Section 4.3.4): because Random Forest already performs close to the ceiling of achievable performance on this dataset while LSTM performs considerably worse, a simple 50/50 average of their probabilities cannot exceed the stronger model's result, and can only match or slightly dilute it.

**Decision: H2 is PARTIALLY ACCEPTED.** The hypothesis is supported when the Hybrid model is compared against the LSTM component, but not supported when compared against the Random Forest component. The hybridization strategy adopted in this study (simple probability averaging) is therefore concluded to improve upon the weaker of its two constituent models without measurably improving upon the stronger one, a finding that is discussed further, together with recommended refinements (weighted averaging, stacked meta-learning), in Sections 4.4.4 and 4.4.5.

### 4.6.3 Testing of Hypothesis Three (H3)

**H3:** *The developed hybrid random forest-LSTM model will demonstrate significant performance in detecting faults in marine machinery.*

**Testing procedure.** Unlike H2, which is a *comparative* hypothesis, H3 concerns the Hybrid model's *absolute* performance. It was tested by comparing the Hybrid model's performance metrics against conventional benchmark thresholds for "strong"/"excellent" classification performance widely used in fault-detection and predictive-maintenance literature, namely an accuracy, precision, recall, F1-score, and ROC-AUC of at least 90% (0.90).

**Decision rule.** H3 is **accepted** if all five of the Hybrid model's performance metrics meet or exceed the 90% (0.90) benchmark threshold.

**Table 4.8: Hybrid model performance versus the 90% benchmark threshold (test set, n = 385)**

| Metric | Benchmark threshold | Hybrid model result | Threshold met? |
|---|---|---|---|
| Accuracy | ≥ 90.00% | 99.74% | Yes |
| Precision (Fault) | ≥ 90.00% | 97.73% | Yes |
| Recall (Fault) | ≥ 90.00% | 100.00% | Yes |
| F1-score (Fault) | ≥ 90.00% | 98.85% | Yes |
| ROC-AUC | ≥ 0.90 | 0.9976 | Yes |

**Interpretation.** The Hybrid model exceeds the 90% benchmark threshold on all five evaluation metrics, most notably achieving a perfect Fault recall of 100% (zero missed faults) on the held-out test set. Given the safety-critical nature of marine machinery operation, where an undetected fault carries a substantially higher operational risk than a false alarm (Section 4.4.1), this result is of particular practical significance. Taken together, the five metrics provide consistent, converging evidence that the developed Hybrid model performs strongly on the fault-detection task it was designed for.

**Decision: H3 is ACCEPTED.**

### Summary of Hypothesis Testing

| Hypothesis | Decision |
|---|---|
| H1: Marine machinery operational data will significantly contribute to accurate fault detection. | **Accepted** |
| H2: There will be significant improvement in fault detection when using the hybrid random forest-LSTM model. | **Partially accepted** (improved over LSTM; not improved over Random Forest) |
| H3: The developed hybrid random forest-LSTM model will demonstrate significant performance in detecting faults in marine machinery. | **Accepted** |

Overall, the hypothesis testing confirms that the marine machinery operational data used in this study is a significant contributor to accurate fault detection (H1), and that the final Hybrid model itself performs strongly and reliably at the fault-detection task in absolute terms (H3). The partial acceptance of H2 is an important and honest finding of this research: it demonstrates that combining Random Forest and LSTM through simple probability averaging is sufficient to substantially outperform a weak sequential model, but is not, on its own, sufficient to improve upon an already high-performing single model. This nuance is discussed further in Section 4.4.4, together with the specific dataset characteristics that likely explain it and the alternative ensembling strategies that could be explored in future work.
