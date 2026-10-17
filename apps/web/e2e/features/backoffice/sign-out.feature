@backoffice @HU-8 @SOLV-101
Feature: Back-office sign-out

  Scenario: Signing out returns to the back-office login
    Given an asesor signed in to the back-office
    When the user signs out of the back-office
    Then the back-office login is visible
