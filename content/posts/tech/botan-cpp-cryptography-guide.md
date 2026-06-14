---
title: "Botan：C++ 密码学库完全指南"
date: "2026-03-31T12:45:00+08:00"
slug: "botan-cpp-cryptography-guide"
description: "全面解析 Botan：C++ 密码学库（3.2k Stars，BSD-2 许可证）。覆盖 TLSv1.3、X.509、AEAD、后量子密码学（ML-KEM、ML-DSA）等完整功能体系。从入门到精通，包含架构分析、原理讲解、C++/Python/C API 使用说明和最佳实践。"
draft: false
categories: ["技术笔记"]
tags: ["Botan", "密码学", "C++", "TLS", "加密", "PKI", "后量子密码学"]
---

Botan：C++ 密码学库完全指南

§ 学习目标

学完本文档后，你将能够：

- 理解 Botan 密码学库的设计目标与核心优势
- 掌握 Botan 的完整功能体系（TLS、PKI、对称加密、哈希等）
- 了解密码学基础概念与算法原理
- 学会在不同平台安装和配置 Botan
- 掌握 C++、C、Python 三种 API 的使用方法
- 理解 PKCS#11、TPM 硬件支持的集成方式
- 学会构建 TLS 服务器、使用证书管理、进行后量子密码学实验
- 掌握性能优化和安全配置的实践建议

---

§ 项目概述

. 什么是 Botan

Botan（官方仓库：[randombit/botan](https://github.com/randombit/botan)）是一个**功能全面的 C++ 密码学库**，采用宽松的 BSD-2-Clause 许可证开源。它的设计目标是成为**生产级密码学的最佳选择**，为开发者提供实现实用系统（如 TLSv1.3、X.509 PKI、现代 AEAD 加密、后量子密码学）所需的全部工具。

Botan 的核心理念：**安全不应该妥协**。通过全面的测试套件（包括自动侧信道检测）确保代码安全可靠，同时保持 API 的易用性和代码的可维护性。

. 核心数据

```
Stars:     3,197（3.2k）
Forks:     644
贡献者:    151 人
提交:     18,837 次
分支:     42 branches
标签:     178 tags
许可证:   BSD-2-Clause
语言:     C++ 91.2%, Python 6.6%, C 1.9%
```

. 版本体系

| 版本 | 状态 | 最新版本 | 发布时间 |
|------|------|---------|---------|
| **Botan 3.x** | 活跃开发 | **3.11.0** | 2026-03-15 |
| **Botan 2.x** | 已停止维护（EOL） | 2.19.5 | 2024-07-08 |

**Botan 3** 采用季度发布策略，通常在每年 2 月、5 月、8 月、11 月的第一个周二发布新版本。

**Botan 2** 已于 2025-01-01 停止维护，不再提供更新。

. 为什么选择 Botan

**完整的功能覆盖**：从 TLS 协议到 X.509 证书，从对称加密到后量子密码学，一个库解决所有密码学需求。

**生产级质量**：通过 OSS-Fuzz 持续模糊测试、自动侧信道检测、详尽的测试套件确保代码质量。

**宽松的许可证**：BSD-2-Clause 允许在商业项目和闭源产品中使用，无需开源你的代码。

**多语言支持**：开箱即用提供 C++、C、Python API，其他语言绑定可通过社区获取。

**模块化构建**：可按需启用/禁用功能，支持 amalgamation 单文件构建。

---

§ 原理分析

. 密码学基础概念

在深入 Botan 之前，理解几个核心密码学概念至关重要：

**对称加密 vs 非对称加密**

对称加密使用相同的密钥进行加密和解密，速度快但密钥分发困难。代表算法：AES、ChaCha20。

非对称加密使用公钥加密、私钥解密，或反之。公钥可自由分发，解决了密钥分发问题。代表算法：RSA、ECDSA、Ed25519。

**哈希函数**

将任意长度的输入映射为固定长度的输出，用于数据完整性校验、密码存储、数字签名。代表算法：SHA-2、SHA-3、BLAKE2。

**消息认证码（MAC）**

验证消息完整性并确认消息来源，类似于签名但使用对称密钥。代表算法：HMAC、Poly1305。

**认证加密（AEAD）**

同时提供加密和完整性保护，是现代密码学通信的标准模式。代表算法：AES-GCM、ChaCha20-Poly1305、AES-SIV。

. TLS 协议原理

TLS（Transport Layer Security）是保护互联网通信的核心协议。Botan 支持 TLSv1.2、TLSv1.3 和 DTLSv1.2。

**TLS 1.3 的关键改进**

- 更快的握手：1-RTT 甚至 0-RTT（无需等待服务器 hello）
- 更强的安全性：移除不安全的密码套件，要求前向保密
- 混合后量子密钥交换：支持 ML-KEM（Kyber）或 FrodoKEM

**Botan TLS 的核心功能**

```
TLSv1.3 握手流程（简化）：
ClientHello（支持密码套件列表）
        │
        ▼
← ServerHello（选择密码套件）+ 证书
        │
        ▼
   密钥交换（ECDHE 或后量子 ML-KEM）
        │
        ▼
   应用数据加密传输
```

. X. PKI 原理

公钥基础设施（PKI）通过证书将公钥绑定到身份，实现可信的身份认证。

**证书链验证**

```
根证书（Root CA）
    │ 签发
    ▼
中间证书（Intermediate CA）
    │ 签发
    ▼
终端实体证书（End Entity Certificate）
    │ 包含公钥和身份信息
    ▼
验证者检查证书有效性、有效期、撤销状态
```

**Botan 支持的功能**

- X.509v3 证书创建和处理
- PKIX 证书路径验证（包括名称约束）
- OCSP（Online Certificate Status Protocol）请求和响应处理
- PKCS#10 证书请求生成和处理
- 访问 Windows、macOS、Unix 系统证书存储
- SQL 数据库支持的证书存储

. 后量子密码学

量子计算机威胁当前 RSA/ECDSA 的安全性。NIST 已标准化的后量子算法：

**签名算法**

| 算法 | 类型 | 用途 |
|------|------|------|
| **ML-DSA**（Dilithium） | 格密码 | 通用签名 |
| **SLH-DSA**（SPHINCS+） | 哈希签名 | 长期签名 |
| **XMSS** | 状态哈希签名 | 哈希签名 |

**密钥封装机制（KEM）**

| 算法 | 类型 | 用途 |
|------|------|------|
| **ML-KEM**（Kyber） | 格密码 | 密钥协商 |
| **FrodoKEM** | 格密码 | 保守选择 |
| **Classic McEliece** | 纠错码 | 最高安全 |

Botan TLS 1.3 已支持使用 ML-KEM 或 FrodoKEM 的混合后量子密钥交换。

---

§ 架构分析

. 代码结构

```
botan/
├── .devcontainer/          # 开发容器配置
├── .github/                 # GitHub Actions CI/CD
├── doc/                     # 文档（RST 格式）
├── src/                     # 源代码
│   ├── botan/              # 主要源码
│   │   ├── cert/          # 证书处理
│   │   ├── cipher/        # 加密算法
│   │   ├── hash/          # 哈希函数
│   │   ├── mac/          # 消息认证码
│   │   ├── tls/          # TLS 协议
│   │   └── utils/         # 工具函数
│   └── build/             # 构建产物
├── configure.py            # 配置脚本（类似 autoconf）
├── pyproject.toml         # Python 包配置
└── README.rst             # 项目说明
```

. 功能模块

**核心模块组织**

| 模块 | 功能 | 代表类/函数 |
|------|------|------------|
| **pubkey** | 公钥算法 | RSA, ECDSA, Ed25519, ML-DSA |
| **keywrap** | 密钥包装 | AES_keywrap |
| **mac** | 消息认证 | HMAC, Poly1305, GMAC |
| **stream** | 流密码 | ChaCha20, Salsa20, RC4 |
| **cipher** | 分组密码 | AES, ARIA, SM4, Threefish |
| **hash** | 哈希函数 | SHA-2, SHA-3, BLAKE2, BLAKE3 |
| **kdf** | 密钥派生 | HKDF, PBKDF2, Argon2, Scrypt |
| **tls** | TLS 协议 | TLS::Context, TLS::Server |
| **x509** | 证书处理 | X509_Certificate, PKCS10_Request |
| **pkcs11** | PKCS#11 接口 | PKCS11::Module, PKCS11::Session |
| **tpm2** | TPM 2.0 接口 | TPM2::Context |

. 构建系统

Botan 使用 Python 编写的 `configure.py` 作为配置系统（类似 autoconf）：

```bash
配置构建（启用所有功能）
python3 configure.py --with-zlib --with-bzip2 --with-lzma

配置构建（最小化构建）
python3 configure.py --without-documentation

使用 CMake（实验性）
mkdir build && cd build
cmake .. -DBOTAN_WITH_TLS=ON -DBOTAN_WITH_X509=ON
```

**可选依赖**

| 依赖 | 功能 | 启用选项 |
|------|------|---------|
| zlib | 压缩支持 | `--with-zlib` |
| bzip2 | 压缩支持 | `--with-bzip2` |
| lzma | 压缩支持 | `--with-lzma` |
| openssl | OpenSSL 互操作 | `--with-openssl` |
| sqlite | 证书存储 | `--with-sqlite3` |
| tpm2 | TPM 支持 | `--with-tpm2` |

. 跨平台支持

Botan 经过测试可在以下平台构建：

**操作系统**

- Linux（Ubuntu、Debian、Fedora、Arch）
- macOS
- Windows（MSVC、MinGW、Cygwin）
- BSD 系列（FreeBSD、OpenBSD）

**编译器**

- GCC 7+
- Clang 6+
- MSVC 2019+

---

§ 功能详解

. TLS 协议

Botan 提供完整的 TLS 实现，支持 TLSv1.2、TLSv1.3、DTLSv1.2。

**基本 TLS 连接（C++）**

```cpp
#include <botan/tls_client.h>
#include <botan/tls_callbacks.h>

class TLSCallbacks : public Botan::TLS::Callbacks {
    void tls_emit_data(const uint8_t data[], size_t size) override {
        // 发送数据到网络
        send_to_network(data, size);
    }
    void tls_record_received(u64 seq, const uint8_t data[], size_t size) override {
        // 处理接收到的应用数据
        process_data(data, size);
    }
};

int main() {
    TLSCallbacks callbacks;
    Botan::TLS::Policy policy;  // 使用默认策略
    Botan::TLS::Session_Manager session_manager;
    Botan::RandomNumberGenerator& rng = Botan::system_rng();

    Botan::TLS::Client client(callbacks, session_manager, policy, rng);

    // 连接到服务器
    client.set_hostname("example.com");
    client.set_port(443);
    client.handshake();

    // 发送请求
    client.send("GET / HTTP/1.1\r\nHost: example.com\r\n\r\n");
}
```

**TLS 1.3 后量子混合密钥交换**

```cpp
#include <botan/tls_policy.h>

class PostQuantumPolicy : public Botan::TLS::Policy {
public:
    std::vector<std::string> allowed_key_exchange_methods() override {
        // 启用 ML-KEM（Kyber）混合密钥交换
        return {
            "ECDH_P256_MLKEM768",
            "ECDH_X25519_MLKEM768",
        };
    }
};
```

. 公钥密码学

**RSA 签名与验证**

```cpp
#include <botan/rsa.h>
#include <botan/pk_sign.h>
#include <botan/pubkey.h>

// 生成密钥
Botan::RSA_PrivateKey rsa_key(rng, 3072);

// 签名
Botan::PK_Signer signer(rsa_key, rng, "EMSA3(SHA-256)");
signer.update(message);
std::vector<uint8_t> signature = signer.signature();

// 验证
Botan::PK_Verifier verifier(rsa_key, "EMSA3(SHA-256)");
verifier.update(message);
bool valid = verifier.check_signature(signature);
```

**Ed25519 签名（更现代、更快）**

```cpp
#include <botan/ed25519.h>

// 生成密钥
Botan::Ed25519_PrivateKey ed_key(rng);

// 签名
Botan::PK_Signer ed_signer(ed_key, rng, "Raw");
ed_signer.update(message);
std::vector<uint8_t> ed_signature = ed_signer.signature();

// 验证
Botan::Ed25519_PublicKey ed_pub(ed_key);
Botan::PK_Verifier ed_verifier(ed_pub, "Raw");
ed_verifier.update(message);
bool ed_valid = ed_verifier.check_signature(ed_signature);
```

**后量子 ML-DSA 签名**

```cpp
#include <botan/ml_dsa.h>

// 生成 ML-DSA-65（对应 AES-192 安全级别）
Botan::MLDSA_PrivateKey mldsa_key(rng, Botan::MLDSA::Mode::MLDSA_65);

// 签名
Botan::PK_Signer mldsa_signer(mldsa_key, rng, "Raw");
mldsa_signer.update(message);
std::vector<uint8_t> mldsa_sig = mldsa_signer.signature();
```

. 对称加密

**AES-GCM 认证加密（推荐）**

```cpp
#include <botan/aead.h>
#include <botan/cipher_mode.h>

// 生成密钥和 IV
Botan::SymmetricKey key(rng, 32);  // 256-bit
Botan::InitializationVector iv(rng, 12);  // 96-bit for GCM

// 创建 cipher
auto enc = Botan::Cipher_Mode::create("AES-256/GCM", Botan::Cipher_Dir::Encryption);
enc->set_key(key);
enc->start(iv);
enc->finish(plaintext, 0);

std::vector<uint8_t> ciphertext = enc->next_vec();
std::vector<uint8_t> mac = enc->mac();  // GCM authentication tag
```

**ChaCha20-Poly1305（现代流密码）**

```cpp
auto chacha = Botan::Cipher_Mode::create("ChaCha20-Poly1305", Botan::Cipher_Dir::Encryption);
chacha->set_key(key);
chacha->start(iv);
chacha->finish(plaintext, 0);
```

. 哈希函数

**基本使用**

```cpp
#include <botan/hash.h>

// SHA-256
auto sha256 = Botan::HashFunction::create("SHA-256");
sha256->update(data);
std::vector<uint8_t> hash = sha256->final();

// BLAKE2b（通常更快）
auto blake2b = Botan::HashFunction::create("BLAKE2b-512");
blake2b->update(data);
std::vector<uint8_t> hash512 = blake2b->final();
```

. 密码哈希（适合存储密码）

**Argon2（目前最佳）**

```cpp
#include <botan/argon2.h>

std::string password = "user_password";
std::string salt = Botan::hex_encode(rng.random_vec(16));

// Argon2id（推荐参数）
std::string hash = Botan::argon2_generate_pbkdf(
    password,
    salt,
    3,      // iterations
    32,     // output length
    1 << 20 // memory (1 MiB)
);

// 验证
bool ok = Botan::argon2_check_pbkdf(hash, password);
```

. X. 证书处理

**证书验证**

```cpp
#include <botan/x509_cert.h>
#include <botan/certstor.h>

// 加载证书
Botan::X509_Certificate cert("server.pem");
Botan::X509_Certificate root("ca.pem");

// 创建验证对象
Botan::Certificate_Store_In_Memory store;
store.add_certificate(root);

Botan::Path_Validation_Result result = Botan::x509_path_validate(
    cert,
    store,
    Botan::Path_Validation_Restrictions::standard(),
    "example.com"  // 验证主机名
);

if (result.successful_validation()) {
    printf("Certificate valid for example.com\n");
}
```

---

§ 使用说明

. 环境要求

- **C++ 编译器**：GCC 7+、Clang 6+、MSVC 2019+
- **Python 3.8+**：用于配置脚本
- **可选依赖**：zlib、bzip2、lzma、OpenSSL、SQLite 等

. 安装方式

**方式一：从包管理器安装**

```bash
Ubuntu/Debian
sudo apt install botanist libbotan-3-dev

Fedora
sudo dnf install botan3 botan3-devel

macOS (Homebrew)
brew install botan

Arch Linux
sudo pacman -S botan
```

**方式二：从源码构建（推荐最新版本）**

```bash
克隆仓库
git clone https://github.com/randombit/botan.git
cd botan

配置构建
python3 configure.py --with-zlib --with-bzip2 --with-lzma

编译
make -j$(nproc)

安装
sudo make install

更新库缓存
sudo ldconfig
```

**方式三：Amalgamation 单文件构建**

适合嵌入式或简化构建：

```bash
python3 configure.py --amalgamation
生成 botan_all.h 和 botan_all.cpp
g++ -o botan_app botan_all.cpp -lz -lbz2 -llzma -pthread
```

. Python API 安装

```bash
使用 pip（需要先构建库）
pip3 install botan3

或从源码安装 Python 绑定
cd botan
python3 setup.py install
```

**Python 使用示例**

```python
from botan import HashFunction, Cipher, PK Signer, TLS

SHA- 哈希
sha256 = HashFunction.create("SHA-256")
sha256.update(b"hello world")
digest = sha256.final()
print(digest.hex())

AES--GCM 加密
key = Cipher.generate_key("AES-256")
enc = Cipher.create("AES-256/GCM/NoPadding")
enc.set_key(key)
ct, tag = enc.encrypt(b"secret message", nonce)
```

. C API 使用

Botan 提供 C 绑定（`botan.h`），适合 C 项目或 FFI 集成：

```c
#include <botan/ffi.h>

botan_pubkey_t pubkey;
botan_load_pubkey(&pubkey, "key.pem");

botan_hash_t hash;
botan_hash_init(&hash, "SHA-256", 0);
botan_hash_update(hash, data, data_len);
uint8_t hash_out[32];
botan_hash_final(hash, hash_out);
botan_hash_destroy(hash);
```

. 命令行工具

Botan 提供功能丰富的 CLI（需在构建时启用）：

```bash
哈希计算
botan hash SHA-256 data.txt

加密文件
botan encrypt AES-256/GCM key.txt plaintext.bin ciphertext.bin

生成随机数
botan rng 32 > random.bin

密钥生成
botan keygen RSA --bits 3072 --output rsa.pem
botan keygen Ed25519 --output ed25519.pem

证书验证
botan verify server.pem --ca-certs ca.pem --hostname example.com
```

---

§ 开发扩展

. 集成 PKCS 硬件安全模块

PKCS#11 是访问加密硬件（如 HSM、智能卡）的标准接口。

```cpp
#include <botan/pkcs11.h>

// 加载 PKCS#11 模块
Botan::PKCS11::Module pkcs11("/usr/lib/librtpkcs11.so");

// 打开会话
Botan::PKCS11::Session session(pkcs11, 0, Botan::PKCS11::Session::RW);

// 登录（如果需要 PIN）
session.login(user_pin, Botan::PKCS11::Session::User);

// 获取私钥
auto private_key = session.get_private_key(key_id);

// 使用私钥签名
Botan::PK_Signer signer(*private_key, rng, "SHA-256");
signer.update(data);
auto signature = signer.signature();
```

. 集成 TPM .

TPM（可信平台模块）是硬件级的安全芯片。

```cpp
#include <botan/tpm2.h>

// 创建 TPM 上下文
Botan::TPM2::Context tpm;

// 加载 EK（认可密钥）
auto ek = tpm.load_public_key("ek.pub");

// 创建 SRK（存储主密钥）
auto srk = tpm.create_srk(rng, "AES-256");
```

. 自定义密码套件

扩展 Botan 支持新的算法或密码套件：

```cpp
// 注册自定义哈希函数
Botan::HashFunction::register_algorithm("MyHash", [](size_t out_len) {
    return std::make_unique<MyHashFunction>();
});

// 使用自定义哈希
auto my_hash = Botan::HashFunction::create("MyHash");
```

. 与 Boost.Asio 集成

Botan TLS 可与 Boost.Asio 异步 I/O 配合使用：

```cpp
#include <botan/tls_server.h>
#include <boost/asio.hpp>

class TLSStream {
    Botan::TLS::Server server;
    boost::asio::ip::tcp::socket socket;

public:
    TLSStream(boost::asio::io_context& io, Botan::TLS::Policy& policy)
        : server(callbacks, session_mgr, policy, rng)
        , socket(io)
    {}

    // 异步读写接口...
};
```

---

§ 实践建议

. 密钥管理

**生成强密钥**

```cpp
// 使用安全的随机数生成器
Botan::AutoSeeded_RNG rng;

// RSA 至少 3072 位（2026 年后推荐 4096 位）
Botan::RSA_PrivateKey rsa_key(rng, 3072);

// ECDSA 使用 P-256 或更高级曲线
Botan::EC_Group secp256r1("secp256r1");
Botan::ECDSA_PrivateKey ecdsa_key(rng, secp256r1);
```

**安全存储密钥**

- 使用加密的 PEM 文件：`Botan::Encrypted_PEM`
- 硬件保护：PKCS#11、TPM
- 定期轮换：建立密钥更新流程

. TLS 配置

**推荐的安全策略（TLS 1.3）**

```cpp
class SecurePolicy : public Botan::TLS::Policy {
public:
    std::vector<uint16_t> allowed_ciphersuites() override {
        return {
            TLS_13_AES_256_GCM_SHA384,
            TLS_13_CHACHA20_256_POLY1305_SHA256,
        };
    }

    std::vector<std::string> allowed_key_exchange_methods() override {
        return {
            "ECDH_P256",
            "ECDH_X25519",
            "ECDH_P256_MLKEM768",  // 后量子混合
        };
    }

    bool allow_tls12() const override { return false; }  // 仅 TLS 1.3
};
```

. 密码学参数选择

**对称加密**

| 算法 | 密钥长度 | 推荐场景 |
|------|---------|---------|
| AES-256-GCM | 256-bit | 通用推荐 |
| ChaCha20-Poly1305 | 256-bit | 移动设备、性能敏感 |
| AES-SIV | 256-bit | 需要确定性的场景 |

**哈希函数**

| 算法 | 输出长度 | 推荐场景 |
|------|---------|---------|
| BLAKE2b | 512-bit | 通用哈希、性能敏感 |
| SHA-3 | 512-bit | 长期存储、监管要求 |
| SHA-256 | 256-bit | 兼容性优先 |

**密码哈希**

| 算法 | 推荐参数 | 内存需求 |
|------|---------|---------|
| **Argon2id** | 3 iterations, 64 MiB | 高 |
| **Scrypt** | 2^20 iterations, 8 MiB | 中 |
| **bcrypt** | cost=12 | 低 |

. 错误处理

```cpp
try {
    Botan::Cipher_Mode::create("AES-256/GCM", Botan::Cipher_Dir::Encryption);
} catch (const Botan::Algorithm_Not_Found& e) {
    // 算法不支持
} catch (const Botan::Invalid_Key_Length& e) {
    // 密钥长度错误
}

// 验证返回值
auto hash = Botan::HashFunction::create("SHA-256");
if (!hash) {
    // 创建失败
}
```

---

§ 常见问题

Q：Botan 与 OpenSSL 比较如何？

| 维度 | Botan | OpenSSL |
|------|-------|---------|
| 许可证 | BSD-2（允许闭源） | Apache 2 + SSLeay |
| C++ API | 原生设计 | C 封装 |
| 后量子密码学 | 内置 ML-KEM, ML-DSA | 通过 OQS |
| 代码质量 | 测试覆盖率更高 | 历史更久 |
| 维护活跃度 | 活跃 | 非常活跃 |

Q：如何验证 Botan 安装正确？

```bash
命令行测试
botan version
botan hash SHA-256 < /dev/urandom | head -c 64

C++ 测试
echo '#include <botan/version.h>
int main(){ printf("%s\n", Botan::version_string()); }' | \
g++ -x c++ -I/usr/include/botan-3 -lbotan-3 -o version - && ./version

Python 测试
python3 -c "from botan import version; print(version)"
```

Q：Botan 支持 Android/iOS 吗？

是的。Android NDK 和 iOS SDK 都经过测试。使用 `configure.py` 交叉编译：

```bash
Android NDK
./configure.py --os=android --cpu=arm64
```

Q：如何贡献代码？

1. 阅读 [CONTRIBUTING.md](https://github.com/randombit/botan/blob/master/CONTRIBUTING.md)
2. Fork 仓库并创建功能分支
3. 确保通过所有测试：`python3 validate.py`
4. 提交 Pull Request

Q：遇到编译错误怎么办？

1. 确保使用支持的编译器版本（GCC 7+、Clang 6+）
2. 检查是否安装了所有必需依赖
3. 查看 [GitHub Issues](https://github.com/randombit/botan/issues)
4. 使用 `configure.py --with-debug-info` 获取详细调试信息

Q：Botan 的安全响应流程是什么？

发现安全漏洞请联系：security@randombit.net

详见：https://botan.randombit.net/security.html

---

§ 总结

Botan 是目前最全面的 C++ 密码学库，通过 BSD-2 许可证允许在商业产品中使用。

**核心优势**：

- 完整功能覆盖：TLS、PKI、对称加密、哈希、后量子密码学
- 生产级质量：OSS-Fuzz、侧信道检测、全面测试
- 多语言 API：C++、C、Python 开箱即用
- 宽松许可证：BSD-2 允许闭源使用
- 活跃维护：季度发布、响应及时

**推荐学习路径**：

1. 从 TLS 客户端/服务器示例开始，理解密码学编程模式
2. 学习证书处理（X.509），掌握 PKI 实践
3. 探索后量子密码学（ML-KEM、ML-DSA），为量子威胁做准备
4. 深入 PKCS#11/TPM 集成，实现硬件级安全

**链接资源**：

- GitHub 仓库：https://github.com/randombit/botan
- 官方文档：https://botan.randombit.net/handbook
- 安全页面：https://botan.randombit.net/security.html
- 发行说明：https://botan.randombit.net/news.html

---

*🦞 文档版本 1.0 | 撰写日期：2026-03-31 | 基于仓库 commit 547c5d7 (2026-03-29)*