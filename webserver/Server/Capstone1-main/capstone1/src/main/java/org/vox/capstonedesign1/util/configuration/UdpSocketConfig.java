package org.vox.capstonedesign1.util.configuration;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.net.*;

@Configuration
public class UdpSocketConfig {

    @Bean
    public DatagramSocket datagramSocket() throws SocketException, UnknownHostException {
        return new DatagramSocket(new InetSocketAddress("0.0.0.0", 9999));
    }
}
