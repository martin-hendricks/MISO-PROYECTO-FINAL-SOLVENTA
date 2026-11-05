@quotation @pendiente @embedded
Feature: Embedded quote and payment

  Scenario: Registration through renewal
    Given a customer ready to register monthly amounts
    When the customer registers, quotes, confirms the local card and issues
    Then the issued policy offers automatic renewal without sending the card
