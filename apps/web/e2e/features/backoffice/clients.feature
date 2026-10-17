@backoffice @HU-8 @SOLV-101
Feature: Back-office client list

  Scenario: The advisor sees the clients served by the BFF
    Given the BFF lists 5 clients
    And an asesor signed in to the back-office
    Then the client list shows the listed clients

  Scenario: No clients shows the empty state
    Given the BFF has no clients
    And an asesor signed in to the back-office
    Then the client list shows the empty state

  Scenario: A failed load can be retried
    Given the BFF fails to list clients
    And an asesor signed in to the back-office
    Then the client list shows the error state
    When the BFF lists 3 clients
    And the asesor retries loading the clients
    Then the client list shows the listed clients
