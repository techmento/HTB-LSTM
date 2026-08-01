# CHAPTER FIVE: SUMMARY, CONCLUSIONS AND RECOMMENDATIONS

## 5.1 Introduction

This chapter presents the concluding summary of the study, drawing together the research problem, objectives, methodology, and major findings established in the preceding chapters. It presents the conclusions reached in relation to each of the study's specific objectives, offers practical recommendations for ship operators, marine engineers, maintenance teams, and future researchers, and outlines the limitations encountered during the course of the study. The chapter closes with suggestions for further research and a brief summary of its content.

## 5.2 Summary of the Study

**Research problem.** Marine machinery — including main engines, generators, and pumps — is central to the safety, reliability, and operational efficiency of ship operations, and timely fault detection is essential to minimising machinery failure, reducing maintenance costs, and safeguarding maritime safety. At Ikraam Sea Line, fault detection has historically relied on traditional, largely reactive methods — routine inspection, alarm systems, and operator observation — which typically identify faults only after machinery has already begun to deteriorate abnormally. Although substantial operational data (engine oil pressure, coolant temperature, exhaust gas temperature, engine speed, and related parameters) is routinely collected, it has not been systematically analysed to support early, intelligent fault detection, resulting in unplanned breakdowns, elevated maintenance costs, voyage delays, and increased safety risk. While hybrid machine learning approaches — combining models such as Random Forest and Long Short-Term Memory (LSTM) networks — have shown promise for improving fault detection accuracy in the wider literature, no such intelligent, data-driven system had previously been developed or evaluated at Ikraam Sea Line.

**Research objectives.** The study was guided by the main objective of developing a hybrid Random Forest and LSTM fault detection system for marine machinery at Ikraam Sea Line, pursued through three specific objectives:

i. To analyse relevant marine machinery operational data for fault detection.
ii. To apply a hybrid Random Forest and Long Short-Term Memory model for fault detection.
iii. To evaluate the performance of the developed hybrid model in fault detection.

**Overview of methodology.** The study followed a structured, four-stage methodology. First, marine machinery operational data was compiled from Ikraam Sea Line's engine-room logbooks, covering readings from two main engines (ME1, ME2) and two generators (GEN1, GEN2). Second, the collected data was preprocessed and prepared for modelling — resolving inconsistent date formats, handling missing sensor values, excluding malformed machine records, and engineering a 12-feature representation combining raw sensor readings with rule-based fault-threshold indicators. Third, three models were developed: a Random Forest classifier operating on individual readings, an LSTM network operating on sequences of ten consecutive readings per machine, and a Hybrid model formed by averaging the fault probabilities produced by the two independently trained models. Fourth, the performance of all three models was evaluated on a common held-out test set using Accuracy, Precision, Recall, F1-score, ROC-AUC, and confusion matrix analysis, with the results used to test the study's three research hypotheses.

## 5.3 Summary of Major Findings

The major findings obtained in Chapter Four are summarised as follows:

- **Findings from the operational data analysis.** The dataset comprised 2,007 machinery readings, exhibiting a pronounced class imbalance (88.5% Normal against 11.5% Fault) consistent with the rarity of genuine fault events in real-world condition-monitoring data. Data preprocessing identified and addressed inconsistent date formats, missing exhaust-temperature readings, malformed machine identifiers, and a small number of physically implausible outlier values, after which 1,921–1,960 valid readings remained for modelling.

- **Relationship between operational parameters and fault detection.** Correlation analysis showed that the five sensor variables were largely independent of one another, with only a weak-to-moderate positive relationship observed between Lubrication Oil Temperature and Coolant Temperature (r = 0.36) — indicating that the sensor variables each carry largely distinct, non-redundant information relevant to fault detection. The five rule-based fault-threshold flags derived from the raw readings proved to be strong, near-deterministic indicators of machinery fault condition.

- **Performance comparison between Random Forest, LSTM, and Hybrid RF-LSTM models.** The Random Forest model substantially outperformed the LSTM model on every evaluation metric. The Hybrid model, formed by averaging the two models' outputs, matched the Random Forest's performance exactly but did not exceed it, since the averaging mechanism could not improve upon an already high-performing model when combined with a considerably weaker one.

- **Results based on evaluation metrics.** On the shared held-out test set (n = 385), the Random Forest and Hybrid models each achieved 99.74% accuracy, 97.73% precision, 100% recall, 98.85% F1-score, and ROC-AUC scores of 0.9993 and 0.9976 respectively, while the LSTM model achieved 68.57% accuracy, 15.79% precision, 41.86% recall, 22.93% F1-score, and a ROC-AUC of 0.7198. Hypothesis testing (Section 4.6) confirmed that the operational data significantly contributes to accurate fault detection (H1, accepted), that the Hybrid model significantly improved on the LSTM component but not on the Random Forest component (H2, partially accepted), and that the developed Hybrid model demonstrates strong absolute fault-detection performance (H3, accepted).

## 5.4 Conclusions

**Objective One — To analyse relevant marine machinery operational data for fault detection.**
The study concludes that marine machinery operational data collected at Ikraam Sea Line — engine speed, lubrication oil pressure, lubrication oil temperature, coolant temperature, and exhaust temperature — holds strong, exploitable value for fault detection when properly preprocessed and engineered. The analysis revealed that raw sensor readings alone are less informative than their combination with rule-derived threshold indicators, and that a data-driven model trained on this combined representation dramatically outperforms a naive baseline that ignores the data altogether. This confirms that a systematic, analytical approach to the machinery's own operational data — rather than reliance on manual inspection alone — provides a sound and significant basis for fault detection at the company.

**Objective Two — To apply a hybrid Random Forest and LSTM model for fault detection.**
The study concludes that a hybrid Random Forest–LSTM fault detection model was successfully developed and applied to the marine machinery operational data, with the Random Forest component modelling individual readings and the LSTM component modelling temporal sequences of readings per machine, combined through probability averaging. The resulting Hybrid model is fully functional and was integrated into a working monitoring dashboard capable of processing both single manual readings and batch file uploads. However, the study also concludes that the specific hybridization strategy employed — simple averaging of the two models' probabilities — improved fault detection substantially relative to the LSTM component alone but did not measurably improve upon the Random Forest component alone, an important nuance for the interpretation of "hybrid" performance in this context and for the design of future hybridization strategies (Section 5.7).

**Objective Three — To evaluate the performance of the developed hybrid model in fault detection.**
The study concludes that the developed Hybrid Random Forest–LSTM model performs strongly and reliably at the fault-detection task, achieving 99.74% accuracy, 97.73% precision, 100% recall, and a 98.85% F1-score, alongside a ROC-AUC of 0.9976, on data the model had not seen during training. Of particular practical significance is the model's perfect recall on the Fault class — no genuine fault in the test data was missed — which directly addresses the operational risk of undetected machinery deterioration identified in the research problem. The evaluation therefore concludes that the hybrid model, as developed, is capable of supporting timely, accurate, and reliable fault detection for marine machinery at Ikraam Sea Line.

## 5.5 Recommendations

Based on the findings of this study, the following recommendations are made:

**For ship operators.** Ship operators at Ikraam Sea Line are recommended to adopt the developed data-driven fault detection dashboard as a complement to, rather than a replacement for, existing inspection and alarm-based practices, using its fault-probability outputs and machine-level alerts to guide inspection priorities and reduce reliance on purely reactive fault identification.

**For marine engineers.** Marine engineers are recommended to make use of the system's rule-based fault-type explanations (e.g. oil pressure anomaly, lubrication oil overheating, coolant overheating) alongside the model's fault probability, so that flagged readings can be diagnosed and verified quickly against the specific operational parameter(s) responsible.

**For maintenance teams.** Maintenance teams are recommended to incorporate the system's historical fault predictions and alerts into preventive maintenance scheduling, shifting maintenance planning from a purely reactive, breakdown-driven basis toward a more proactive, condition-informed one.

**For future researchers.** Future researchers are recommended to validate and extend the developed models in close collaboration with marine engineering domain experts, to prioritise the collection of higher-quality, higher-volume, and more diverse fault event data (Section 5.6), and to explore more sophisticated hybridization strategies — such as weighted averaging or learned meta-classifiers — capable of yielding hybrid models that measurably exceed their strongest individual component, rather than merely matching it.

## 5.6 Limitations of the Study

The following limitations were encountered during the course of this study:

- **Limited dataset size.** The dataset comprised only 2,007 machinery readings in total, and as few as 1,921 sequences were available for LSTM training — a comparatively small sample for training a robust deep learning model.

- **Availability of real-time sensor data.** The study relied on historical operational data compiled from engine-room logbooks rather than live, continuously streaming sensor data, limiting the extent to which the developed models could be validated under genuine real-time operating conditions.

- **Limited fault occurrence records.** Genuine fault events represented only 11.5% of the dataset (231 of 2,007 readings), constraining the diversity of fault patterns available for the models — and particularly the LSTM component — to learn from.

- **Simulation-based modelling approach.** The models were developed, trained, and evaluated on historical, previously recorded data rather than deployed and tested within a live operational environment aboard the vessel, meaning the reported performance reflects retrospective evaluation rather than field-validated, real-time performance.

## 5.7 Suggestions for Further Research

Building on the limitations identified above, the following areas are suggested for further research:

- **Development of real-time fault detection systems.** Future work should extend the current batch/manual-entry monitoring dashboard toward a system capable of continuous, real-time fault detection as machinery readings are generated.

- **Integration of IoT-based sensors for continuous monitoring.** The incorporation of Internet of Things (IoT) sensor networks aboard vessels would enable continuous, automated data collection, reducing reliance on manually compiled logbook records and increasing both the volume and timeliness of available data.

- **Use of larger marine machinery datasets.** Future studies should seek to incorporate operational data from a larger number of vessels, machines, and time periods, including a greater number and diversity of genuine fault events — particularly gradually-developing faults not captured by simple sensor-threshold breaches.

- **Improvement of hybrid deep learning approaches.** Future research should investigate more sophisticated methods of combining Random Forest and LSTM outputs — such as weighted averaging or stacked meta-learning models — building on the finding of this study (Section 4.4.4) that simple probability averaging alone was not sufficient to produce a hybrid model that exceeds its strongest individual component.

## 5.8 Chapter Summary

This chapter presented a summary of the research problem, objectives, and methodology, together with a synthesis of the major findings reported in Chapter Four. Conclusions were drawn against each of the study's three specific objectives, confirming that the marine machinery operational data at Ikraam Sea Line significantly contributes to accurate fault detection, that a hybrid Random Forest–LSTM model was successfully developed and applied, and that the resulting model demonstrates strong, reliable fault-detection performance — most notably, perfect recall on the Fault class in the held-out test data. Recommendations were offered for ship operators, marine engineers, maintenance teams, and future researchers, and the limitations of the study — principally its limited dataset size, reliance on historical rather than real-time data, limited fault occurrence records, and simulation-based modelling approach — were outlined alongside corresponding directions for further research.
