from django.conf import settings

contract = """
pragma solidity ^0.4.24;

contract Wallet {
    address public admin;
    uint public deposit;
 
    constructor () public {
        admin = msg.sender;
        deposit = 0;
    }
    
    modifier adminOnly {
        require(msg.sender == admin);
        _;
    }
    
    function () payable public {
        deposit = deposit + msg.value;
        admin.transfer(msg.value);
    }
}
"""
name = "Wallet"
