from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import MCPServerConfig, MCPTool, MCPExecutionLog
import mcpserver.mcp_client

User = get_user_model()

class MCPExecutionApprovalTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        
        self.server_config = MCPServerConfig.objects.create(
            user=self.user,
            name='Test Server',
            server_type='stdio',
            is_active=True,
            connection_status='connected',
            require_approval=True
        )
        
        self.tool = MCPTool.objects.create(
            server_config=self.server_config,
            tool_name='test_tool',
            description='A test tool'
        )

    def test_execute_tool_requires_approval(self):
        """
        Test that executing a tool on a server with require_approval=True
        logs a pending execution log and returns 202 Accepted.
        """
        url = reverse('mcp-tool-execute', kwargs={'pk': self.tool.pk})
        data = {
            'tool_id': self.tool.pk,
            'arguments': {'param1': 'value1'},
            'chat_thread_id': 'thread-123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['message'], 'Tool execution requires user approval.')
        
        # Verify execution log was created
        log_id = response.data['execution_id']
        exec_log = MCPExecutionLog.objects.get(pk=log_id)
        self.assertEqual(exec_log.status, 'pending')
        self.assertEqual(exec_log.tool, self.tool)
        self.assertEqual(exec_log.input_params, {'param1': 'value1'})
        self.assertEqual(exec_log.chat_thread_id, 'thread-123')

    @patch('mcpserver.mcp_client.MCPClientManager.execute_tool')
    def test_approve_action_executes_pending_tool(self, mock_execute):
        """
        Test that calling the approve endpoint on a pending execution log
        triggers the tool execution, updates the status, and returns the result.
        """
        mock_execute.return_value = {'success': True, 'content': [{'type': 'text', 'text': 'Success!'}]}
        
        exec_log = MCPExecutionLog.objects.create(
            user=self.user,
            tool=self.tool,
            tool_name=self.tool.tool_name,
            server_name=self.server_config.name,
            input_params={'param1': 'value1'},
            status='pending'
        )
        
        url = reverse('mcp-log-approve', kwargs={'pk': exec_log.pk})
        response = self.client.post(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['result'], {'success': True, 'content': [{'type': 'text', 'text': 'Success!'}]})
        
        # Check database log update
        exec_log.refresh_from_db()
        self.assertEqual(exec_log.status, 'success')
        self.assertEqual(exec_log.output_result, {'success': True, 'content': [{'type': 'text', 'text': 'Success!'}]})
        
        # Check tool usage stats
        self.tool.refresh_from_db()
        self.assertEqual(self.tool.usage_count, 1)

    def test_reject_action_cancels_pending_tool(self):
        """
        Test that calling the reject endpoint cancels a pending tool execution.
        """
        exec_log = MCPExecutionLog.objects.create(
            user=self.user,
            tool=self.tool,
            tool_name=self.tool.tool_name,
            server_name=self.server_config.name,
            input_params={'param1': 'value1'},
            status='pending'
        )
        
        url = reverse('mcp-log-reject', kwargs={'pk': exec_log.pk})
        response = self.client.post(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['status'], 'cancelled')
        
        # Check database log update
        exec_log.refresh_from_db()
        self.assertEqual(exec_log.status, 'cancelled')
        self.assertEqual(exec_log.error_message, 'Rejected by user')

    def test_actions_fail_for_non_pending_logs(self):
        """
        Test that approve and reject endpoints fail for non-pending logs.
        """
        statuses = ['running', 'success', 'error', 'cancelled']
        for s in statuses:
            exec_log = MCPExecutionLog.objects.create(
                user=self.user,
                tool=self.tool,
                tool_name=self.tool.tool_name,
                server_name=self.server_config.name,
                input_params={'param1': 'value1'},
                status=s
            )
            
            # Approve should fail
            url_approve = reverse('mcp-log-approve', kwargs={'pk': exec_log.pk})
            response = self.client.post(url_approve, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            
            # Reject should fail
            url_reject = reverse('mcp-log-reject', kwargs={'pk': exec_log.pk})
            response = self.client.post(url_reject, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
