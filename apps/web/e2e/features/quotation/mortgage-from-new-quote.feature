@quotation @HU-105 @SOLV-229
Feature: Mortgage life from Nueva cotización

  Scenario: Vida hipotecario continues in the profiled offer
    Given a customer on Nueva cotización
    When the customer quotes Vida hipotecario
    Then the mortgage is saved and the consent opens with the amounts filled
    And authorizing shows each profiling step before the offer
