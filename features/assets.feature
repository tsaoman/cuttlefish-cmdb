Feature: Assets

  Scenario: Bob owns an asset
    Given I have an asset belonging to Bob
     When I list the assets
     Then I will see Bob's asset
