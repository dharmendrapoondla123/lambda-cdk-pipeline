

#!/usr/bin/env python3
import aws_cdk as cdk
from cdk.lambda_stack import LambdaStack
from cdk.pipeline_stack import PipelineStack

app = cdk.App()
lambda_stack = LambdaStack(app, "LambdaStack")
PipelineStack(app, "PipelineStack", lambda_stack_name=lambda_stack.stack_name)
app.synth()
