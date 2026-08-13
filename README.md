# Weighted Adaptive Traffic Signal Controller (WATSC): A Rule-Based Adaptive Traffic Signal Control System Using SUMO and TraCI

## Overview

This repository contains the implementation of the **Weighted Adaptive Traffic Signal Controller (WATSC)** developed as part of an MSc research project at Dublin City University.

The project presents a lightweight rule-based adaptive traffic signal controller that dynamically allocates green signal time using real-time traffic conditions obtained from the Simulation of Urban Mobility (SUMO) through the Traffic Control Interface (TraCI). The proposed controller is evaluated against a conventional Fixed-Time Controller (FTC) under multiple traffic demand scenarios.

## Project Features

- Rule-based adaptive traffic signal control
- Integration of SUMO with Python using TraCI
- Dynamic signal timing based on:
  - Queue length
  - Vehicle count
  - Cumulative waiting time
- Performance comparison with a Fixed-Time Controller
- Evaluation under:
  - Light traffic
  - Medium traffic
  - Heavy traffic
  - Unbalanced traffic
- Automatic generation of performance graphs and comparison summaries

## Technologies Used

- SUMO (Simulation of Urban Mobility)
- Python
- TraCI (Traffic Control Interface)
- Pandas
- NumPy
- Matplotlib
- Git and GitHub

## Repository Structure

```text
src/
    Python controllers
    Analysis scripts
    Graph generation

sumo/
    Network files
    Route files
    Simulation configuration files

results/
    CSV datasets
    Performance comparison summaries
    Generated graphs

## Performance Metrics

The controllers are evaluated using:

- Average waiting time
- Maximum waiting time
- Average queue length
- Maximum queue length
- Vehicle throughput

## Project Outcome

Experimental evaluation demonstrated that the proposed Weighted Adaptive Traffic Signal Controller (WATSC) consistently reduced vehicle waiting time and queue length while maintaining or improving vehicle throughput when compared with a conventional Fixed-Time Controller. The controller achieved its best performance under Medium, Heavy and Unbalanced traffic conditions, demonstrating the effectiveness of a lightweight rule-based adaptive traffic signal control strategy.

## Repository

GitHub Repository:

https://github.com/sameer1030/Final-project

The expected outcome of this project is a working simulation-based smart traffic management system capable of dynamically adjusting traffic signals according to traffic conditions. The project aims to demonstrate improvements in traffic efficiency when compared with conventional fixed-time signal systems.
