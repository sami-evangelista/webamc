iptables -P FORWARD DROP
iptables -P INPUT   ACCEPT
iptables -P OUTPUT  ACCEPT
iptables -A INPUT -i eth1 -j DROP
iptables -A FORWARD -m state --state ESTABLISHED -j ACCEPT
iptables -A FORWARD -o eth1 -m state --state NEW -p tcp -j ACCEPT
iptables -A FORWARD -o eth1 -m state --state NEW -p tcp --dport 400 -j DROP
iptables -A FORWARD -p icmp -j ACCEPT
