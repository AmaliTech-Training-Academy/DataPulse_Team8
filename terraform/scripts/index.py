import boto3
import os

def handler(event, context):
    cluster = os.environ.get('CLUSTER_NAME')
    services_str = os.environ.get('SERVICES', '')
    services = [s.strip() for s in services_str.split(',') if s.strip()]
    desired_count = int(os.environ.get('DESIRED_COUNT', 0))
    action = os.environ.get('ACTION', 'UNKNOWN')
    
    print(f"Action: {action}, Cluster: {cluster}, Services: {services}, Desired Count: {desired_count}")
    
    if not cluster or not services:
        print("Missing cluster name or services list")
        return {'statusCode': 400, 'body': 'Missing config'}

    ecs = boto3.client('ecs')
    
    for service in services:
        try:
            print(f"Updating service {service} to desired count {desired_count}")
            ecs.update_service(
                cluster=cluster,
                service=service,
                desiredCount=desired_count
            )
        except Exception as e:
            print(f"Error updating service {service}: {str(e)}")
    
    return {
        'statusCode': 200,
        'body': f"Successfully initiated {action} for {len(services)} services"
    }
