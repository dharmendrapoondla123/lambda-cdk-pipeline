from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
)
from constructs import Construct

class LambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.lambda_fn = _lambda.Function(
            self, "sample-cdk-lambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda_functions"),
            function_name="sample-cdk-lambda"
        )
