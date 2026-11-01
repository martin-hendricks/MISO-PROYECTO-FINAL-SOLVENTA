@access @HU-102 @SOLV-226
Feature: Customer sign-up

  Scenario: Sign-up without camera
    Given the customer comes from language and region or from "Crear cuenta" on login
    When the customer fills in name, document, email and password
    Then the customer continues to data consent
    And no document photo or biometrics are requested

  Scenario: Already have an account
    Given the customer is on sign-up
    When the customer chooses to sign in
    Then the customer goes to the web login
