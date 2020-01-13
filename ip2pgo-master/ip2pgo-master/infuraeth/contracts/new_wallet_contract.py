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
        require(msg.value >= 0.005 * 1 ether);
        deposit = deposit + msg.value - 0.005 * 1 ether;
        admin.transfer(msg.value);
    }
}
"""
name = "Wallet"
