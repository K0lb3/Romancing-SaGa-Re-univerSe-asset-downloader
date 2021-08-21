### Introduction

As you might have noticed, the easy and traditional way, so using a simple proxy, to spoof the network communication of the game with the game server doesn't work.
While the traffic with the asset server, as well as the advertisement and report servers, does show up this way, the important one, with the actual game server doesn't.

### Network Redirection

The reason for this is, that the game ignores the proxy setting. This is also called proxy-unaware and requires a different setup for spoofing the traffic.
Since the traffic can't be influenced directly, we have to convince the game to connect to our proxy instead of the game server. This can be done by editing the host file, using a fake DNS server, or by using arp spoofing. 

In this case, we will use [Hosts Go](https://play.google.com/store/apps/details?id=dns.hosts.server.change), as it even works on unrooted devices and is therefore useable even for other apps, that refuse to run on emulators. A more common tool for this approach is [ProxyDroid](https://play.google.com/store/apps/details?id=org.proxydroid&hl=en), which requires root.


To set up Hosts Go, we have to open it and add an entry to it via ``Hosts Editor``.
The domain has to be the game server you're playing on, so
```
Asia - production-api.rs-as.aktsk.com
Europe - production-api.rs-eu.aktsk.com
US - production-api.rs-us.aktsk.com
```
For other games, Wireshark can be used to determine the game API.


The IP address has to be the local IP address of the computer running the proxy, which is the same as the one for the normal proxy setup.
After the entry is added, click on its check-box and click #Toggle. Now return to Hosts Go's main screen via back, activate ``Host Change Switch`` and press Start.
Hosts Go will then create a local VPN in which it will answer DNS requests for the specified address by itself instead of consulting a DNS server, therefore redirecting the game to our proxy.

### Proxy Setup

So far we managed to make the game send the requests destined for the game server to our local server instead. Sadly our computer doesn't really know how to handle those requests itself, so we have to work on that now.

What we have to do is set up a so-called reverse proxy, which passes incoming traffic to other servers.
Since we know the target of the incoming traffic, the game API, as well as the port, 443 (HTTPS), we simply have to tell setup our proxy as reverse proxy, that listens on the local port 443 and proxies the requests to the remote API, the game API, at port 443.
As our proxy is in the middle of the game and server now and is a communication partner of each side, it can decrypt the traffic.

If you actively followed this small guide, you should now see incoming failed traffics of the game.
The reason the requests fail is not a problem in the setup, but that the game uses SSL pinning - long story short, it checks the used certificate for the SSL session and notices that it's not a certificate that is supposed to be used.

### Disabling SSL Pinning

This is obviously bad and has to be fixed. Sadly the [SSL pinning bypass using objection](https://gowthamr1.medium.com/android-ssl-pinning-bypass-using-objection-and-frida-scripts-f8199571e7d8) doesn't work, as the game uses its own SSL pinner that has to be disabled. So, time to boot up [Ghidra](https://github.com/NationalSecurityAgency/ghidra) to look for the pinner, so that it can be removed or at least make it always return that the used certificate is valid. Since the game is a Unity game, we can use [Il2CppDumper](https://github.com/Perfare/Il2CppDumper) to get some juicy metadata like function names, which makes finding the SSL pinner way easier than without.
I recommend using the script ghidra_with_struct.

Once Ghidra finished the auto analysis and we imported the metadata, we check the functions/symbol tree via string search. Words worth searching for are, 
- ssl
- pin
- pem
- cer
- crt
- x509

In this case, the custom SSL pinner of the game is named ``Mikoto.Network.PinningCertificateVerifier`` and consists of
- ctor - a constructor
- GetDnsNames
- IsValid
- ValidateCertificateDns
- ValidateDns
- ValidatePublicKey

By checking the label of said class, we notice that it's referred to by ``Mikoto.ApplicationBootProcess$$OnLateBoot``, which tells us that the class is at least used, so we're at the correct place.
After looking through all functions of the verifier, we notice that all functions besides isValid are called by isValid. That means, that as long as we make isValid always return true, the SSL pinning is disabled.

First of all, we go to the end of the isValid function and click on ``return 0`` in the decompiled code view. The listing/assembly view now moved to that place as well.
We will see the following instruction
`` 
00dbc8a4 01 00 a0 e3     mov        r0,#0x0
``
This instruction sets the return value to 0, so false. Since we want the function to return true, we have to edit this instruction and make it return 1, true.
To do this, we have to click on the instruction, select ``Patch Instruction``, change ``#0x0`` to ``#0x1``, and then hit enter.

Since the function can also return the return from validatePublicKey, the same procedure has to be done within that function.
An alternative would be to make the isValid function never reach this branch by changing the branch condition.

After all, modifications are done, we use File->Export Program to export our patched libil2cpp. Make sure to use the format ELF there.

### Installing the patched libil2cpp.so

Depending on whether or not you have a device with root, this can be more or less tricky.
If you have a rooted device, simply replace the original libil2cpp in ``/data/app/com.square_enix.android_googleplay.RSRSWW-1/lib/{arch}``.

If you don't have a rooted device, you have to patch the modified libil2cpp into the apk, resign it and install it.

### Conclusion

Now that you disabled ssl pinning and set up the proxy, you can start sniffing the traffic of the game with the actual api.

Have fun!