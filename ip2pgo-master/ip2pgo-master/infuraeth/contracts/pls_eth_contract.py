from django.conf import settings
from directapp import ieo

contract = """
pragma solidity ^0.4.24;

contract Wallet {
    address public admin;
    address public ieo;
    uint public deposit;
 
    constructor (address _ieo) public {
        admin = msg.sender;
        ieo = _ieo;
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
constructors = {
    '_ieo': ieo.IEO['PLS']['ethwallet'] 
}
