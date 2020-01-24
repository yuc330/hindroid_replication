# Hindroid Replication


- [Hindroid Replication](#hindroid-replication)
  - [1. Malware Classification](#1-malware-classification)
  - [2. Datasets](#2-datasets)
    - [2.1 Datasets from Hindroid Paper](#21-datasets-from-hindroid-paper)
    - [2.2 Datasets Used in Replication](#22-datasets-used-in-replication)
      - [Advantages](#advantages)
      - [Limitations](#limitations)
  - [3. Obtaining Data](#3-obtaining-data)
  - [4. Data Ingestion Process](#4-data-ingestion-process)
    - [4.1 Data Origination and Legal Issues](#41-data-origination-and-legal-issues)
    - [4.2 Data Privacy](#42-data-privacy)
    - [4.3 Schema](#43-schema)
    - [4.4 Pipeline](#44-pipeline)
    - [4.5 Applicability](#45-applicability)


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

## 3. Obtaining Data

As mentioned above, the benign app samples will be collected and downloaded from apkpure.com. Roughly following the data collecting process explained in *Hindroid* paper, we plan to obtain a number, not too far from our malware sample size, of Android applications published on apkpure over some time span. To do this, we first obtain `sitemap.xml`, which consists of all the apps that are on apkpure.com. Then, through sampling process that will be further confirmed later, we will determine our sample of benign apps. Some sampling methods include random sampling from `sitemap.xml`, sampling same amount of apps in each category, and obtaining a section of consecutively listed applications in the `sitemap.xml`. 

After we have decided our benign app samples, we will download their **Dex** files from apkpure.com, decompile them to Smali code files, and obtain all API calls in Smali code. We will then extract features from these API call data.

## 4. Data Ingestion Process

This section will explain the whole data ingestion process and relevant details.

### 4.1 Data Origination and Legal Issues

Our dataset originates from mainly two sources, apkpure.com for the benign apps and privates sources for malwares. There will be less concern regarding obtaining malware samples as this is under authorization of the owner. We also avoid raising any legal issues as the apk files downloaded from apkpure.com are for a personal project with educational purpose. According to the [terms of use](https://apkpure.com/terms.html), apkpure suggests that visitors of it can **only use the site for personal use**. 

### 4.2 Data Privacy

As apkpure.com is a public platform for Android application installation, and all applications are open, we avoid violating data privacy. However, we will encrypt related app and developers names to be careful.

### 4.3 Schema

Our decompiled apk files will be organized in a way shown below to keep Smali code files and AndroidManifest.xml only. In this way, we can save more storage space.

``` source
  data/
  |-- Grubhub/
  |   |-- AndroidManifest.xml
  |   |-- Smali/
  |   |   |-- .smali
  |   |   |-- ...
  |-- Amtrak/
  |   |-- AndroidManifest.xml
  |   |-- Smali/
  |   |   |-- .smali
  |   |   |-- ...
  ```

### 4.4 Pipeline

- Create `apps.csv` that contains basic information for each app with `sitemap.xml`. This spreadsheet is used for sampling methods except for random sampling, and will include information of the application's url, publish date, last update date for now.

- Sample from `sitemap.xml` according to `apps.csv`. For now, we will use random sampling and create a sample with size similar to malware sample size.

- Create `confic.json`, an example shown below, based on our chosen sample of benign applications. Download applications in our sample from apkpure.com.
```json
  {
  "urls": [
      "https://apkpure.com/grubhub-local-food-delivery-restaurant-takeout/com.grubhub.android",
      "https://apkpure.com/amtrak/com.amtrak.rider"
      ],
  "path": "data"  
  }
  ```

  - With apktool, we eventually decompile downloaded **Dex** files to folders with Smali code files. We then organize the decompiled files according to [schema](#43-schema).

  - All procedures above are for benign app sample in our datasets. Malware samples will be given directly as Smali code files.

### 4.5 Applicability

Possible similar data sources include other third-party Android application store and websites, or even the Google Playstore. However, our pipeline may have limited applicability depending on what other data sources we are using. For Google Playstore, it is harder to scrape and download application files as an account is required. On the other hand, our pipeline can possibly raise legal issues or privacy concern depending on each site's policy. It is important to check each Android application store or website before employing our pipeline.

