from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cpactions,
    aws_codebuild as codebuild,
    aws_s3 as s3,
    SecretValue,
    aws_iam as iam,
)
from constructs import Construct

class PipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, lambda_stack_name: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        artifact_bucket = s3.Bucket(self, "ArtifactBucket")

        source_output = codepipeline.Artifact("SourceOutput")
        build_output = codepipeline.Artifact("BuildOutput")

        # CodeBuild project that will synth the CDK app and output CloudFormation template
        build_project = codebuild.PipelineProject(self, "SynthProject",
            environment=codebuild.BuildEnvironment(build_image=codebuild.LinuxBuildImage.STANDARD_6_0),
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml")
        )

        # Give CodeBuild permission to read/write to S3 and perform cdk synth related calls
        build_project.add_to_role_policy(iam.PolicyStatement(
            actions=["s3:*","sts:AssumeRole","cloudformation:DescribeStacks","cloudformation:ListStacks"],
            resources=["*"]
        ))

        pipeline = codepipeline.Pipeline(self, "CICDPipeline",
            artifact_bucket=artifact_bucket
        )

        # GitHub Source Action: update owner/repo and use Secret in SecretsManager named "github-token"
        # source_action = cpactions.GitHubSourceAction(
        #     action_name="GitHub_Source",
        #     owner="dharmendrapoondla123",
        #     repo="dharmendrapoondla123/lambda-cdk-pipeline",
        #     branch="main",
        #     #oauth_token=SecretValue.secrets_manager("github-token"),
        #     connection_arn="arn:aws:codeconnections:ap-south-1:347156581188:connection/3712b2a1-b005-4a2f-9ff2-5db33267c2af",
        #     output=source_output,
        #     trigger=cpactions.GitHubTrigger.WEBHOOK
        # )

        source_action = cpactions.CodeStarConnectionsSourceAction(
        action_name="GitHub_Source",
        owner="dharmendrapoondla123",
        repo="lambda-cdk-pipeline",  # ✅ Correct repo name only
        branch="main",
        connection_arn="arn:aws:codeconnections:ap-south-1:347156581188:connection/3712b2a1-b005-4a2f-9ff2-5db33267c2af",
        output=source_output,
        )



        pipeline.add_stage(stage_name="Source", actions=[source_action])

        # Build / Synth stage
        build_action = cpactions.CodeBuildAction(
            action_name="CDK_Build",
            project=build_project,
            input=source_output,
            outputs=[build_output]
        )

        pipeline.add_stage(stage_name="Build", actions=[build_action])

        # Deploy stage uses CloudFormation action to deploy the synthesized template
        deploy_action = cpactions.CloudFormationCreateUpdateStackAction(
            action_name="CFN_Deploy",
            stack_name=lambda_stack_name,  # deploy to the same logical name as LambdaStack
            template_path=build_output.at_path(f"{lambda_stack_name}.template.json"),
            admin_permissions=True
        )

        pipeline.add_stage(stage_name="Deploy", actions=[deploy_action])
