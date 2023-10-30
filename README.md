# awessomest_phish

This method was originally posted in a [blog](https://blog.christophetd.fr/phishing-for-aws-credentials-via-aws-sso-device-code-authentication/)  Christophe Tafani-Dereeper. This tool serves as an implementation of Christophe Tafani-Dereeper's research and an expansion of Sebastian Mora's work, [awsssome_phish](https://github.com/sebastian-mora/awsssome_phish#awsssome_phish) to automate account persistence. 

## awessomest_phish overview

When a user visits the phishing URL a lambda function starts sso-oicd authentication, and the user is redirected to a device authenication URL to the approve the OIDC request.  Additionally when the user clicks on the phishing link, a simple StepFunctions statemachine is invoked in the background and it attempts to create an OIDC token every 30 seconds until the 6 minute device authenication URL times out.  If the user accepts the OIDC/Device Code Flow request, the SFN statemachine will then create AWS session tokens from the OIDC token for every account and permmission set the user has access to.

Session tokens for each permission set are then sent to a SQS queue, which is in turns invokes lambda functions (gain_persistence) in parallel to push a Cloudformation stack to gain persistence victim's account(s) using the phished credentials.  The CloudFormation stack pushed to the victim's account creates a role with admin priviliges the attacker's account has access to assume.  Once the CFN stack is successfully published to the victim's account, an SNS message is emailed to the attacker and the ARN of the role in the victum's account is written to DynamoDB.

![unnamed](https://github.com/chuckiewonder/most_awsssome_phish/assets/11650102/173ce411-8d36-487b-9d9c-5d451cf64d12)


##  Requirements

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* [Python 3 installed](https://www.python.org/downloads/)


##  Install / Deploy

1) Install SAM CLI
2) Update the samconfig.toml configuration file:
    STARTURL = The Victim's SSO URL
    REGION = <Region>
    STAGE = API GW STage (e.g. Prod)
    SNSRECIPIENT = The email address for notifications
3) sam build
4) sam deploy
5) Upload ./victim_cfn/victim_cfn.yaml to the S3 bucket deployed to he Attacker's account (awssupportbucket-<attacker's account id>)

