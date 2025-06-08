package org.vox.capstonedesign1.testutil;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.SocketException;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

public class MockDatagramSocket extends DatagramSocket {

    private final BlockingQueue<DatagramPacket> packetQueue = new LinkedBlockingQueue<>();
    private boolean closed = false;

    public MockDatagramSocket() throws SocketException {
        super(0); // 임의 포트 사용
    }

    public void injectPacket(DatagramPacket packet) {
        packetQueue.offer(packet);
    }

    @Override
    public void receive(DatagramPacket packet) {
        try {
            DatagramPacket incoming = packetQueue.take(); // 큐에서 가져옴
            packet.setData(incoming.getData(), 0, incoming.getLength());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    @Override
    public void close() {
        closed = true;
    }

    @Override
    public boolean isClosed() {
        return closed;
    }
}
