# Hindroid Replication

## Project Status

Project|Status
---|---
Data Ingestion|In progress



- [Hindroid Replication](#hindroid-replication)
  - [Project Status](#project-status)
  - [1. Malware Classification](#1-malware-classification)
  - [2. Datasets](#2-datasets)
    - [2.1 Datasets from Hindroid Paper](#21-datasets-from-hindroid-paper)
    - [2.2 Datasets Used in Replication](#22-datasets-used-in-replication)
      - [Advantages](#advantages)
      - [Limitations](#limitations)
  - [3. Data Generating Process](#3-data-generating-process)


## 1. Malware Classification

Android system has always been known for its openness, attracting a great amount of developers to design and implement Android applications (apps). However, this also brings serious problems to cybersecurity by introducing a channel for attackers to publish malwares that damage users. In *Hindroid* paper, it is mentioned that for every five Android applications, one malware hides itself among benign apps. To create more friendly environment and experiences for Android users, efforts have been put in to classify harmful apps from benign ones before they could have hurt users. 

The developers of *Hindroid* software also expect their product to contribute to cybersecurity by classifying harmful applications from the benign ones. They employ machine learning algorithms to investigate the Smali code decompiled from `.dex` extension files (for Android applications) to look for potential relationships among API calls, or Application Programming Interface calls.

## 2. Datasets

This section will explain datasets used for *Hindroid* development and datasets we are planning to use during replication. Data is in the form of interpretable Smali code, which is decompiled from a `.dex` extension file either downloaded from apkpure.com or obtained from other sources.

### 2.1 Datasets from Hindroid Paper

To conduct experiments, *Hindroid* developers use two training datasets, one with 1,834 Android apps and the other with 30,000 Android apps, and a test set of 500 Android apps, all roughly equally divided between malicious and benign apps, all obtained from Comodo Cloud Security Center. These apps were all collected during the first two months of 2017.

### 2.2 Datasets Used in Replication

Our dataset consists of:
1. Benign Android Application from apkpure.com that I will collect and decompile to Smali Code
2. Malware samples provided as Smali Code

Our benign part of data will represent a population of Android applications generally published on apkpure.com in recent years if we have sampled our data well for the benign ones, and is thus reliable as they are all actual published Android application. On the other hand, our malwares sample represent recognized malwares in history. Although reliable, they may be out of date and thus unable to include the newest developed malwares. This results in one of the limitation mentioned later in [limitations](#limitaions). Thus, the malware part of our data may not be exactly relevant to our question as we would like to use our program/software to classify future possible malwares for platforms. Nevertheless, our  historical data of malwares provide a general start for our development.

#### Advantages

1. Smali code files are decompiled from actual Android application **dex** files downloaded from apkpure.com. By using the platform, we not only obtain real-world perpective during training, but also improve efficiency as apkpure.com offers easier download process and publishes fewer applications compared to Playstore. 
2. Performing classification on Smali codes improves efficiency by reducing the time needed to run through applications and also avoiding possible damage from malwares.
3. The training data includes both benign and harmful applications, and is also expected to include them with generally the same shares. The balanced dataset results in better classification performance during training process.

#### Limitations

1. The collection process of app files from apkpure may result in unbalanced number of applications in each categories and also in proportions of paid or free apps (since we only download free apps).
2. There is no guarantee that all apps we collect from apkpure.com are benign, and may mislead our classification training process.
3. Our own dataset will contain newer apps collected but older malwares obtained before, causing a time discrepancy.

## 3. Data Generating Process

As mentioned above, the benign app samples will be collected and downloaded from apkpure.com. Roughly following the data collecting process explained in *Hindroid* paper, we plan to obtain a number, not too far from our malware sample size, of Android applications published on apkpure over some time span. To do this, we first obtain `sitemap.xml`, which consists of all the apps that are on apkpure.com. Then, through sampling process that will be further confirmed later, we will determine our sample of benign apps. Some sampling methods include random sampling from `sitemap.xml`, sampling same amount of apps in each category, and obtaining all applications during a certain timeframe. 

After we have decided our benign app samples, we will download their **Dex** files from apkpure.com, decompile them to Smali code files, and obtain all API calls in Smali code. We will then extract features from these API call data.
