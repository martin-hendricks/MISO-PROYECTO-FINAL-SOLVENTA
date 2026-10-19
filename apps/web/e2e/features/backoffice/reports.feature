@backoffice @pendiente
Feature: Back-office regulatory and reinsurance reports

  @HU-62 @SOLV-155
  Scenario: Export for the regulator
    Given the compliance role in the portal
    When the user exports policies and claims
    Then the user gets an internal extract, not the SFC format
    And the file is produced by the stub adapter

  @HU-63 @SOLV-156
  Scenario: Extract for the reinsurer
    Given the operations role in the portal
    When the user generates the portfolio or loss extract
    Then the core is not coupled to ACORD
    And the stub adapter defines the file
