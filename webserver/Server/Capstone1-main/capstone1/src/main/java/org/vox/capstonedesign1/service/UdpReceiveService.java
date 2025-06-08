package org.vox.capstonedesign1.service;

import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.vox.capstonedesign1.util.handler.AgentSignalHandler;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.util.Arrays;

@Slf4j
@Component
@RequiredArgsConstructor
public class UdpReceiveService {

    private final DatagramSocket datagramSocket;
    private final AgentSignalHandler agentSignalHandler;

    @PostConstruct
    public void start() {
        Thread thread = new Thread(this::startUdpServer);
        thread.setDaemon(true);
        thread.start();
    }

    public void startUdpServer(){
        log.info("UDP 서버 시작됨. 포트: {}", datagramSocket.getLocalPort());
        byte[] buffer = new byte[16834];
        while (!datagramSocket.isClosed()) {
            try {
                DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                datagramSocket.receive(packet);
                byte[] data = Arrays.copyOfRange(packet.getData(), 0, packet.getLength());
                agentSignalHandler.handleMessage(data);
            } catch (IOException e) {
                log.error("UDP 수신 중 오류 발생", e);
            }
        }
    }
}
