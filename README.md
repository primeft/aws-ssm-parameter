# AWS SSM Parameter

## Purpose

Often there are times where you have values that are used during runtime or environment specific that that exists on infrastructure.  This actions primary use case is for that.

This actions purpose is to create SSM Parameters for you in a Github workflow.  It actually will check to see if the SSM Parameter exists, if it does not exist it will then create a new parameter.  If the parameter already exists, it checks to make sure its the same as the value you specify.  If it is not, it will go ahead and update that value to be what you have specified.

## How To Use This Action

Currently this option takes three different inputs/arguments.  Two of them are required and one is optional.

<!--doc_begin-->
## Inputs
|Input|Description|Default|Required|
|-----|-----------|-------|:------:|
|`name`|AWS SSM Parameter Name|n/a|yes|
|`description`|AWS SSM Parameter Description|n/a|yes|
|`value`|AWS SSM Parameter Value|n/a|no|
|`tier`|AWS SSM Parameter Tier|`Standard`|no|
|`type`|AWS SSM Parameter Type|`String`|no|
|`file-path`|File to read the value from|n/a|no|
## Outputs
None
<!--doc_end-->

### SSM Parameter Naming Constraints

* Parameter names are case sensitive.
* A parameter name must be unique within an AWS Region.
* A parameter name can't be prefixed with "aws" or "ssm" (case-insensitive).
* Parameter names can include only the following symbols and letters: `a-zA-Z0-9_.-/`
* A parameter name can't include spaces.
* Parameter hierarchies are limited to a maximum depth of fifteen levels.

### SSM Parameter Tiers

Parameter Store includes standard parameters and advanced parameters. You individually configure parameters to use either the standard-parameter tier (the default tier) or the advanced-parameter tier.

[Check out the AWS documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html) about the differences between the two different tiers.

## Examples

As as emample, suppose you want to create a SSM Parameter in Parameter Store but you do not want to actually expose that secret in your workflow.  This is where you would be creating a Github Secret where you are storing that value and then using the Github secrets context to have that injected during runtime. In the example below, `description` is optional and not required but is recommended.

<!-- x-release-please-start-version -->
```yaml
- name: Awesome Client Secret - SSM Parameter
  uses: primeft/aws-ssm-parameter@v1.0.0
  with:
      name: /awesome/clientSecret
      value: ${{ secrets.AWESOME_CLIENT_SECRET }}
      description: Super Secret - Do Not Tell Anyone
```
<!-- x-release-please-end -->

The action does not require you to specify a `tier` when using the action.  If you do not specify one, it will default your parameter to be an `Standard` type parameter.

If that does not work for you, you can also specify `Standard` or `Advanced`.  Check out the [AWS documentation on tiers](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html#ps-default-tier) for more details if you want more information on selecting a tier.  See example below.

<!-- x-release-please-start-version -->
```yaml
- name: Awesome Client Secret - SSM Parameter
  uses: primeft/aws-ssm-parameter@v1.0.0
  with:
      name: /awesome/clientSecret
      value: ${{ secrets.AWESOME_CLIENT_SECRET }}
      description: Super Secret - Do Not Tell Anyone
      tier: Advanced
```
<!-- x-release-please-end -->
