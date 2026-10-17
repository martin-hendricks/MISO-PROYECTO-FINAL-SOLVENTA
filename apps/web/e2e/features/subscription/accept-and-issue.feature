@subscription @pendiente @HU-114 @SOLV-238
Feature: Customer acceptance and issuance

  Scenario: Happy path
    Given a valid unused offer
    When the customer accepts it
    Then the customer sees the issuance progress without the destinations top navigation
    And on success the customer sees the issued policy with number and validity
    And "Ver mi póliza" opens the policy detail
    And "Ir al inicio" opens Inicio
