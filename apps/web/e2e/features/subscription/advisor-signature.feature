@subscription @HU-17 @SOLV-110 @SOLV-112
Feature: Advisor issuance with a failed signature

  Scenario: The signature fails
    Given an asesor on an offer the core approved
    When the asesor issues it and the electronic signature fails
    Then the Emisión step of the stepper is marked as an error
    And the asesor sees the reason the signature failed
    And no policy is shown as issued
    And the asesor can quote another product for the same customer
