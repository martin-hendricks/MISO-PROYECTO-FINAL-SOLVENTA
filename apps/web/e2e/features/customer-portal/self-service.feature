@customer-portal @pendiente @HU-66 @SOLV-159
Feature: Customer self-service

  Scenario: Without an advisor
    Given the customer is signed in
    When the customer consults and manages the basics
    Then the customer does not need an advisor
    And the customer cannot renew, modify or cancel a policy
