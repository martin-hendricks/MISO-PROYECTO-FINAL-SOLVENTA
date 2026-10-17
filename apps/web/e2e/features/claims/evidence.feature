@claims @pendiente @HU-100 @SOLV-225
Feature: Claim evidence

  Scenario: Dropzone
    Given the customer is on the claim evidence step
    When the customer attaches a file
    Then the notice can be sent with that evidence

  Scenario: Optional browser location
    Given the evidence dropzone
    When the customer chooses "Usar ubicación del navegador" and allows it
    Then a coordinate is stored
    And if the customer blocks it the notice continues without a geotag
