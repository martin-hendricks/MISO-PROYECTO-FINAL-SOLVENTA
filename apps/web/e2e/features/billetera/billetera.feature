@billetera
Feature: Customer wallet

  Scenario: Deposits and total
    Given the customer has two deposits
    When the customer opens the wallet
    Then the wallet shows both deposits and the total

  Scenario: Empty wallet
    Given the customer has no deposits
    When the customer opens the wallet
    Then the wallet explains that a deposit appears when Solventa pays

  Scenario: Wallet error and retry
    Given the wallet read fails
    When the customer opens the wallet
    Then the wallet offers a retry and no zero total
    When the customer retries the wallet
    Then the wallet shows both deposits and the total
