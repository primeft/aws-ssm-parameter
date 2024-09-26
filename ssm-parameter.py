#!/usr/bin/env python3

import argparse

import boto3
from botocore.exceptions import ClientError

"""
    Check to see if a AWS SSM Parameter exists
    If it does not exist, create it
    If it does exist, check to see if the value is up to date and update it if not

    Returns:
        Status of the operation
"""

parser = argparse.ArgumentParser(description="Check for AWS SSM Parameter")

parser.add_argument("--name", type=str, help="AWS SSM Parameter Name")
parser.add_argument("--value", type=str, help="AWS SSM Parameter Value")
parser.add_argument("--description", type=str, help="AWS SSM Parameter Description")
parser.add_argument("--tier", type=str, help="The parameter tier to assign to a parameter.")
parser.add_argument("--type", type=str, help="AWS SSM Parameter Type")

args = parser.parse_args()


def check_value_ssm_parameter(
    parameter_name: str,
    parameter_value: str,
    parameter_description: str,
    parameter_tier: str,
    parameter_type: str,
) -> bool:
    """
    Check to see if the value of a AWS SSM Parameter is up to date

    URLs:
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.describe_parameters # noqa
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameter

    Parameters:
        parameter_name (str): AWS SSM Parameter Name
        parameter_value (str): AWS SSM Parameter Value
        parameter_description (str): Optional AWS SSM Parameter Description
        parameter_tier (str): Optional The parameter tier to assign to a parameter.
        parameter_type (str): Optional AWS SSM Parameter Type

    Returns:
        True or False (bool): [Value of the SSM parameter for the client token]
    """

    ssm = boto3.client("ssm")

    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        value = response["Parameter"]["Value"]
        print("Parameter Exists, checking parameter details....")
        print(f" - Parameter Value: {parameter_name}")

        response = ssm.describe_parameters(
            ParameterFilters=[
                {"Key": "Name", "Values": [parameter_name]},
            ],
        )

        parameter_details = response["Parameters"][0]

        try:
            description = parameter_details["Description"]
        except KeyError:
            print("Description not found")
            description = ""

        tier = parameter_details["Tier"]
        type = parameter_details["Type"]

        if type != parameter_type:
            raise ValueError(f"Cannot change parameter type from {type} to {parameter_type}")
        elif value == parameter_value and description == parameter_description and tier == parameter_tier:
            print(" - Verified parameter details are current.")
            return True
        else:
            print(" - Parameter details need to be updated.")
            return False
    except ClientError as e:
        # If the parameter does not exist, return None
        if e.response["Error"]["Code"] == "ParameterNotFound":
            print("Parameter does not exist and needs to be created.")
            return False
        else:
            raise


def put_ssm_parameter(
    parameter_name: str,
    parameter_value: str,
    parameter_description: str,
    parameter_tier: str,
    parameter_type: str,
) -> bool:
    """
    Create or Update a AWS SSM Parameter

    URLs:
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.put_parameter

    Parameters:
        parameter_name (str): AWS SSM Parameter Name
        parameter_value (str): AWS SSM Parameter Value
        parameter_description (str): Optional AWS SSM Parameter Description
        parameter_tier (str): Optional The parameter tier to assign to a parameter.
        parameter_type (str): Optional AWS SSM Parameter Type

    Returns:
        True or False (bool): [Value of the SSM parameter for the client token]
    """

    ssm = boto3.client("ssm")

    try:
        ssm.put_parameter(
            Name=parameter_name,
            Value=parameter_value,
            Description=parameter_description,
            Type=parameter_type,
            Overwrite=True,
            Tier=parameter_tier,
            DataType="text",
        )
        print(" - Parameter successfully created/updated.")
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ParameterLimitExceeded":
            print("Parameter Limit Exceeded")
            print(
                "Parameter Store API calls can't exceed the maximum allowed API request rate per account and per Region."  # noqa
            )
            print("https://docs.aws.amazon.com/general/latest/gr/ssm.html")
            return False
        if error_code == "InvalidAllowedPatternException":
            print("Invalid Allowed Pattern")
            print(
                "https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_PutParameter.html#API_PutParameter_RequestSyntax"  # noqa
            )
            return False
        if error_code == "TooManyUpdates":
            print("There are concurrent updates for a resource that supports one update at a time.")
            return False
        else:
            raise


value_response = check_value_ssm_parameter(
    parameter_name=args.name,
    parameter_value=args.value,
    parameter_description=args.description,
    parameter_tier=args.tier,
    parameter_type=args.type,
)

if value_response is False:
    # value needs to be updated
    put_ssm_parameter(
        parameter_name=args.name,
        parameter_value=args.value,
        parameter_description=args.description,
        parameter_tier=args.tier,
        parameter_type=args.type,
    )
