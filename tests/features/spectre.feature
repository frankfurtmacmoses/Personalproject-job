# tests/features/spectre.feature
#
# Author: Harrison Lee
# Date: 06/27/2019
# Description: Utilizing Cucumber framework to test Watchmen (Spectre).

Feature: Monitor S3 ensuring Georgia Tech Feed is properly transferred

    Scenario: Check Georgia Tech Feed for correct file
        Given the Spectre Watchman
        When Spectre monitors S3
        Then it should return a result explaining success or failure
