iptables -P FORWARD DROP
iptables -A FORWARD -i eth0 -j ACCEPT
iptables -A FORWARD -i eth1 -m state --state ESTABLISHED -j ACCEPT
