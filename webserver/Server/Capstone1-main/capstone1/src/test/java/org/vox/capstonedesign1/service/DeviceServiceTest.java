//package org.vox.capstonedesign1.service;
//
//import org.junit.jupiter.api.Test;
//import org.springframework.beans.factory.annotation.Autowired;
//import org.springframework.boot.test.context.SpringBootTest;
//import org.springframework.boot.test.mock.mockito.MockBean;
//import org.springframework.test.context.ActiveProfiles;
//import org.vox.capstonedesign1.util.handler.AgentSignalHandler;
//
//import java.net.DatagramSocket;
//
//import static org.assertj.core.api.Assertions.assertThat;
//
//@SpringBootTest
//@ActiveProfiles("test")
//class DeviceServiceTest {
//
//    @MockBean
//    private DatagramSocket datagramSocket;
//
//    @MockBean
//    private UdpReceiveService udpReceiveService;
//
//    @MockBean
//    private AgentSignalHandler agentSignalHandler;
//
//    @Autowired
//    private DeviceService deviceService;
//
//    @Test
//    void 디바이스시리얼넘버반환테스트() {
//
//        //given
//        Long deviceId = 123L;
//        String expected = "ABC123";
//
//        //when
//        String serialNumber = deviceService.resolveDeviceSerialNumber(deviceId);
//
//        //then
//        assertThat(serialNumber).isNotNull();
//        assertThat(serialNumber).isEqualTo(expected);
//    }
//}
