from aws_cdk import (
    Stack,
    RemovalPolicy,
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

        # ✅ Artifact bucket for CodePipeline
        artifact_bucket = s3.Bucket(
            self,
            "ArtifactBucket",
            bucket_name="my-cdk-artifact-bucket",
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,  # Keep artifacts safe
            auto_delete_objects=False,             # Must be False when RETAIN
        )

        # Define pipeline artifacts
        source_output = codepipeline.Artifact("SourceOutput")
        build_output = codepipeline.Artifact("BuildOutput")

        # ✅ CodeBuild project to synth CDK app
        build_project = codebuild.PipelineProject(
            self,
            "SynthProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
        )

        # ✅ Allow CodeBuild to access AWS services
        build_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:*", "sts:AssumeRole", "cloudformation:*"],
                resources=["*"],
            )
        )

        # ✅ Create CodePipeline using artifact bucket
        pipeline = codepipeline.Pipeline(
            self,
            "CICDPipeline",
            artifact_bucket=artifact_bucket,
            pipeline_type=codepipeline.PipelineType.V2
        )

        # ✅ Source stage (GitHub via CodeStar Connection)
        source_action = cpactions.CodeStarConnectionsSourceAction(
            action_name="GitHub_Source",
            owner="dharmendrapoondla123",
            repo="lambda-cdk-pipeline",
            branch="main",
            connection_arn="arn:aws:codeconnections:ap-south-1:347156581188:connection/3712b2a1-b005-4a2f-9ff2-5db33267c2af",
            output=source_output,
        )

        pipeline.add_stage(stage_name="Source", actions=[source_action])

        # ✅ Build / Synth stage
        build_action = cpactions.CodeBuildAction(
            action_name="CDK_Build",
            project=build_project,
            input=source_output,
            outputs=[build_output],
        )
        pipeline.add_stage(stage_name="Build", actions=[build_action])

        # ✅ Deploy stage (deploy Lambda stack)
        deploy_action = cpactions.CloudFormationCreateUpdateStackAction(
            action_name="CFN_Deploy",
            stack_name=lambda_stack_name,
            template_path=build_output.at_path(f"{lambda_stack_name}.template.json"),
            admin_permissions=True,
        )
        pipeline.add_stage(stage_name="Deploy", actions=[deploy_action])
