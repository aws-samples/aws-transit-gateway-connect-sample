# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
import re
import json
import time

import boto3
import cfnresponse


def lambda_handler(event, context):
    print(boto3.__version__)
    print('REQUEST RECEIVED:\n')
    print(json.dumps(event))
    response_data = {}
    try:
        ec2 = boto3.client('ec2')
        properties = event['ResourceProperties']
        if event['RequestType'] == 'Create':
            tgw_connect_peer = ec2.create_transit_gateway_connect_peer(
                TransitGatewayAttachmentId=properties['TransitGatewayAttachmentId'],
                TransitGatewayAddress=properties['TransitGatewayAddress'],
                PeerAddress=properties['PeerAddress'],
                BgpOptions={
                    'PeerAsn': int(properties['PeerAsn'])
                },
                InsideCidrBlocks=[
                    properties['InsideCidrBlocks'],
                ]
            )['TransitGatewayConnectPeer']
            peer_id = tgw_connect_peer['TransitGatewayConnectPeerId']
            __wait_for_status(peer_id, 'available', ec2)
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, peer_id)
            return
        if event['RequestType'] == 'Delete':
            if re.match("tgw-connect-peer-[a-zA-Z0-9]+", event['PhysicalResourceId']):
                ec2.delete_transit_gateway_connect_peer(
                    TransitGatewayConnectPeerId=event['PhysicalResourceId']
                )
                __wait_for_status(event['PhysicalResourceId'], 'deleted', ec2)
                cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, event['PhysicalResourceId'])
                return
            else:
                cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, event['PhysicalResourceId'])
                return
        if event['RequestType'] == 'Read':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, event['PhysicalResourceId'])
            return
        if event['RequestType'] == 'Update':
            if re.match("tgw-connect-peer-[a-zA-Z0-9]+", event['PhysicalResourceId']):
                ec2.delete_transit_gateway_connect_peer(
                    TransitGatewayConnectPeerId=event['PhysicalResourceId']
                )
                __wait_for_status(event['PhysicalResourceId'], 'deleted', ec2)
            tgw_connect_peer = ec2.create_transit_gateway_connect_peer(
                TransitGatewayAttachmentId=properties['TransitGatewayAttachmentId'],
                TransitGatewayAddress=properties['TransitGatewayAddress'],
                PeerAddress=properties['PeerAddress'],
                BgpOptions={
                    'PeerAsn': int(properties['PeerAsn'])
                },
                InsideCidrBlocks=[
                    properties['InsideCidrBlocks'],
                ]
            )['TransitGatewayConnectPeer']
            peer_id = tgw_connect_peer['TransitGatewayConnectPeerId']
            __wait_for_status(peer_id, 'available', ec2)
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, peer_id)
            return
    except Exception as e:
        response_data = {'error': str(e)}
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data, False, str(e))
        return


def __wait_for_status(peer_id, status, ec2_client):
    while True:
        state = ec2_client.describe_transit_gateway_connect_peers(
            TransitGatewayConnectPeerIds=[peer_id]
        )['TransitGatewayConnectPeers'][0]['State']
        if state == status:
            break
        else:
            time.sleep(10)
