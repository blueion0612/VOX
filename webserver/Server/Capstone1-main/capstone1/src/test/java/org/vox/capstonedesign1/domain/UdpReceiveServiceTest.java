package org.vox.capstonedesign1.domain;

import org.junit.jupiter.api.Test;
import org.vox.capstonedesign1.testutil.MockDatagramSocket;
import org.vox.capstonedesign1.util.handler.UdpMessageHandler;

import java.net.DatagramPacket;

import static org.mockito.Mockito.*;

class UdpReceiveServiceTest {

    @Test
    void UDP메시지_Handler에_전달하는지_테스트() throws Exception {
//        UdpMessageHandler mockHandler = mock(UdpMessageHandler.class);
//        MockDatagramSocket mockSocket = new MockDatagramSocket();
//        UdpReceiver receiver = new UdpReceiver(mockSocket, mockHandler);
//        receiver.start();
//        String message = "{\"deviceId\":1,\"statusId\":3,\"timeStamp\":\"2025-04-13T12:26:38\"}";
//        byte[] testData = message.getBytes("UTF-8");
//        DatagramPacket packet = new DatagramPacket(testData, testData.length);
//        mockSocket.injectPacket(packet);
//        Thread.sleep(300);
//        verify(mockHandler, times(1)).handleMessage(eq(message));
    }
}
