ip tunnel add gre1 mode gre remote 10.10.0.1 local 10.192.10.10 ttl 255
ip addr add 169.254.7.1/29 dev gre1
ip link set gre1 up

iptables -F; iptables -t nat -F; iptables -t mangle -F
iptables -t nat -A POSTROUTING -o eth0 -j SNAT --to 10.192.10.10
echo "net.ipv4.ip_forward = 1" | tee -a /etc/sysctl.conf
sysctl -p