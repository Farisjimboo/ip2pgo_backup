from django.conf import settings

contract = """
pragma solidity ^0.4.24;

contract ERC_alt {
    function transfer(address to, uint amount) public;
}

contract ERC20 {
    function transfer(address to, uint amount) public returns (bool success);
    function balanceOf(address tokenOwner) public constant returns (uint balance);
}

contract ERC20Wallet {
    address public admin;
 
    constructor () public {
        admin = msg.sender;
    }
    
    modifier adminOnly {
        require(msg.sender == admin);
        _;
    }
    
    function transfer(address token, address wallet, uint amount) public adminOnly {
        ERC20(token).transfer(wallet, amount);
    }

    function transfer_alt(address token, address wallet, uint amount) public adminOnly {
        ERC_alt(token).transfer(wallet, amount);
    }

    function getBalance(address token) public constant returns (uint balance) {
        return ERC20(token).balanceOf(address(this));
    }
}
"""
name = "ERC20Wallet"
