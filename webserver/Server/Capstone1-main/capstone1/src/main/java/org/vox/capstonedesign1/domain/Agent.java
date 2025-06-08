package org.vox.capstonedesign1.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Agent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "agent_name", nullable = false, unique = true)
    private String agentName;

    @ManyToOne
    @JoinColumn(name = "squad_id", nullable = false)
    private Squad squad;

    @OneToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "device_serial_number", referencedColumnName = "device_serial_number", nullable = true)
    private Device device;
}
